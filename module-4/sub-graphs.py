# The most critial thing to understand is how graphs communicate.
# They do that by overlaping state keys
# Se eu quero que grafos filhos tenham acesso a valores do grafo pai, basta eu adicionar a key do 
# state do grafo pai como keys no state dos grafos filhos
# Da mesma forma, se eu quiser acessar valores dos filhos, basta colocar a mesma key no state do pai

from typing import TypedDict, Optional, List, Annotated, Dict
import operator

class Log(TypedDict):
  id: str
  question: str
  docs: Optional[List]
  answer: str
  grade: Optional[int]
  grader: Optional[str]
  feedback: Optional[str]

# Subgraph 1
from langgraph.graph import START, END, StateGraph

class FailureAnalysisState(TypedDict):
  cleaned_logs: List[Log]
  failures: List[Log]
  fa_summary: str
  processed_logs: List[str]

class FailureAnalysisOutputState(TypedDict):
  fa_summary: str
  processed_logs: List[str]

def get_failures(state):
  """Get logs that contain a failure"""
  cleaned_logs = state["cleaned_logs"]
  failures = [log for log in cleaned_logs if "grade" in log]
  return {"failures": failures}

def generate_summary(state):
  """Generate summary of failures"""
  failures = state["failures"]
  # Add fxn: fa_summary = summarize(failures)
  fa_summary = "Poor quality retrieval of Chroma documentation."
  return {"fa_summary": fa_summary, "processed_logs": [f"failure-analysis-on-log-{failure["id"]}" for failure in failures]}

fa_builder = StateGraph(state_schema=FailureAnalysisState, output_schema=FailureAnalysisOutputState)
fa_builder.add_node("get_failures", get_failures)
fa_builder.add_node("generate_summary", generate_summary)
fa_builder.add_edge(START, "get_failures")
fa_builder.add_edge("get_failures", "generate_summary")
fa_builder.add_edge("generate_summary", END)
fa_subgraph = fa_builder.compile()

# Subgraph 2

class QuestionSummarizationState(TypedDict):
  cleaned_logs: List[Log]
  qs_summary: str
  report: str
  processed_logs: List[str]

class QuestionSummarizationOutputState(TypedDict):
  report: str
  processed_logs: List[str]

def generate_summary(state):
  cleaned_logs = state["cleaned_logs"]
  # Add fxn: qs_summary = summarize(generate_summary)
  qs_summary = "Questions focused on usage of ChatOllama and Chroma vector store."
  return {"qs_summary": qs_summary, "processed_logs": [f"summary-on-log-{log["id"]}" for log in cleaned_logs]}

def send_to_slack(state):
  qs_summary = state["qs_summary"]
  # Add fxn: report = report_generation(qs_summary)
  report = "foo bar baz"
  return {"report": report}

qs_builder = StateGraph(state_schema=QuestionSummarizationState, output_schema=QuestionSummarizationOutputState)
qs_builder.add_node(generate_summary)
qs_builder.add_node(send_to_slack)
qs_builder.add_edge(START, "generate_summary")
qs_builder.add_edge("generate_summary", "send_to_slack")
qs_builder.add_edge("send_to_slack", END)
qs_subgraph = qs_builder.compile()

# Defining the parent Graph
class EntryGraphState(TypedDict):
  raw_logs: List[Log]
  cleaned_logs: Annotated[List[Log], operator.add] # This will be used by BOTH sub-graphs
  fa_summary: str # This will only be generated in the fa_subgraph
  report: str # This will only be generated in the qs_subgraph
  processed_logs: Annotated[List[int], operator.add] # This will be generated in BOTH sub-graphs, that's why we need a reducer, because both will write in the same key

# We need a reducer for cleaned_logs even if it isn't modified in the subgraphs, it is because
# the output state of the subgraphs will contain all keys, even if they are unmodified
# To fix that we can defined output schemas that does not contain the cleaned_logs key, then that collision won't happen
class EntryGraphState(TypedDict):
  raw_logs: List[Log]
  cleaned_logs: List[Log]
  fa_summary: str # This will only be generated in the fa_subgraph
  report: str # This will only be generated in the qs_subgraph
  processed_logs: Annotated[List[int], operator.add] # This will be generated in BOTH sub-graphs, that's why we need a reducer, because both will write in the same key

def clean_logs(state):
  #Get logs
  raw_logs = state["raw_logs"]
  # Data cleaning raw_logs -> docs
  cleaned_logs = raw_logs
  return {"cleaned_logs": cleaned_logs}

entry_builder = StateGraph(EntryGraphState)
entry_builder.add_node("clean_logs", clean_logs)
entry_builder.add_node("question_summarization", qs_subgraph)
entry_builder.add_node("failure_analysis", fa_subgraph)

entry_builder.add_edge(START, "clean_logs")
entry_builder.add_edge("clean_logs", "failure_analysis")
entry_builder.add_edge("clean_logs", "question_summarization")
entry_builder.add_edge("failure_analysis", END)
entry_builder.add_edge("question_summarization", END)

entry_graph = entry_builder.compile()

question_answer = Log(
    id="1",
    question="How can I import ChatOllama?",
    answer="To import ChatOllama, use: 'from langchain_community.chat_models import ChatOllama.'",
)

question_answer_feedback = Log(
    id="2",
    question="How can I use Chroma vector store?",
    answer="To use Chroma, define: rag_chain = create_retrieval_chain(retriever, question_answer_chain).",
    grade=0,
    grader="Document Relevance Recall",
    feedback="The retrieved documents discuss vector stores in general, but not Chroma specifically",
)

response = entry_graph.invoke({"raw_logs": [question_answer, question_answer_feedback]})
print(response)