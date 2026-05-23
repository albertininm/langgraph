import operator
from typing import TypedDict, Any, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.errors import InvalidUpdateError
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

class State(TypedDict):
  # The operator.add reducer fn makes this append-only
  state: str

class ReturnNodeValue:
  def __init__(self, node_secret: str):
    # Guarda o valor nessa variavel quando a classe é instanciada
    self._value = node_secret
  
  # Quando o grafo passa pelo nó "a", "b", "c" ou "d", essa função é automaticamente executada recebendo o state como parâmetro
  # Visto que todos os nós do grafo recebem o state como parâmetro
  def __call__(self, state: State) -> Any:
    print(f"Adding {self._value} to {state["state"]}")
    return {"state": [self._value] }
  
# builder = StateGraph(State)

# builder.add_node("a", ReturnNodeValue("I'm A"))
# builder.add_node("b", ReturnNodeValue("I'm B"))
# builder.add_node("c", ReturnNodeValue("I'm C"))
# builder.add_node("d", ReturnNodeValue("I'm D"))

# builder.add_edge(START, "a")
# builder.add_edge("a", "b")
# builder.add_edge("b", "c")
# builder.add_edge("c", "d")
# builder.add_edge("d", END)

# graph = builder.compile()

# result = graph.invoke({"state": []})
# print(result)

# Now, let's run b and c in parallel

# builder = StateGraph(State)

# builder.add_node("a", ReturnNodeValue("I'm A"))
# builder.add_node("b", ReturnNodeValue("I'm B"))
# builder.add_node("c", ReturnNodeValue("I'm C"))
# builder.add_node("d", ReturnNodeValue("I'm D"))

# builder.add_edge(START, "a")
# builder.add_edge("a", "b")
# builder.add_edge("a", "c")
# builder.add_edge("b", "d")
# builder.add_edge("c", "d")
# builder.add_edge("d", END)

# graph = builder.compile()
# try:
#   result = graph.invoke({"state": []})
#   print(result)
# except InvalidUpdateError as e:
#   print(f"An error ocurred: {e}")

# This throws "An error ocurred: At key 'state': Can receive only one value per step. Use an Annotated key to handle multiple values.""
# Which means we could have these parallel steps if we weren't updating the same key
# To update the same key, we need to have a reducer and annotate the state key

# class State(TypedDict):
#   # The operator.add reducer fn makes this append-only
#   state: Annotated[list, operator.add]

# builder = StateGraph(State)

# builder.add_node("a", ReturnNodeValue("I'm A"))
# builder.add_node("b", ReturnNodeValue("I'm B"))
# builder.add_node("c", ReturnNodeValue("I'm C"))
# builder.add_node("d", ReturnNodeValue("I'm D"))

# builder.add_edge(START, "a")
# builder.add_edge("a", "b")
# builder.add_edge("a", "c")
# builder.add_edge("b", "d")
# builder.add_edge("c", "d")
# builder.add_edge("d", END)

# graph = builder.compile()
# try:
#   result = graph.invoke({"state": []})
#   print(result)
# except InvalidUpdateError as e:
#   print(f"An error ocurred: {e}")
# Now it works!

# Now let's test with one of the branch with more steps than the other
# We'll see that before reaching the end Node, we will wait for all the branches to be done

# class State(TypedDict):
#   # The operator.add reducer fn makes this append-only
#   state: Annotated[list, operator.add]

# builder = StateGraph(State)

# builder.add_node("a", ReturnNodeValue("I'm A"))
# builder.add_node("b", ReturnNodeValue("I'm B"))
# builder.add_node("b2", ReturnNodeValue("I'm B2"))
# builder.add_node("c", ReturnNodeValue("I'm C"))
# builder.add_node("d", ReturnNodeValue("I'm D"))

# If we do it this way, they will run at the same time
# builder.add_edge(START, "a")
# builder.add_edge("a", "b")
# builder.add_edge("a", "c")
# builder.add_edge("b", "b2")
# builder.add_edge("b2", "d")
# builder.add_edge("c", "d")
# builder.add_edge("d", END)

# If we do this instead, it will wait before running D
# builder.add_edge(START, "a")
# builder.add_edge("a", "b")
# builder.add_edge("a", "c")
# builder.add_edge("b", "b2")
# builder.add_edge(["b2", "c"], "d")
# builder.add_edge("d", END)

# graph = builder.compile()
# try:
#   result = graph.invoke({"state": []})
#   print(result)
# except InvalidUpdateError as e:
#   print(f"An error ocurred: {e}")

# We saw that nodes in the same state can't be controlled the order they run
# Let's see it's possible to choose the order by defining a reducer

# def sorting_reducer(left, right):
#   """Combines and sorts the values in a list"""
#   if not isinstance(left, list):
#     left = [left]
#   if not isinstance(right, list):
#     right = [right]
#   return sorted(left+right, reverse=False)

# class State(TypedDict):
#   # The operator.add reducer fn makes this append-only
#   state: Annotated[list, sorting_reducer]

# builder = StateGraph(State)

# builder.add_node("a", ReturnNodeValue("I'm A"))
# builder.add_node("b", ReturnNodeValue("I'm B"))
# builder.add_node("b2", ReturnNodeValue("I'm B2"))
# builder.add_node("c", ReturnNodeValue("I'm C"))
# builder.add_node("d", ReturnNodeValue("I'm D"))

# builder.add_edge(START, "a")
# builder.add_edge("a", "b")
# builder.add_edge("a", "c")
# builder.add_edge("b", "b2")
# builder.add_edge(["b2", "c"], "d")
# builder.add_edge("d", END)

# graph = builder.compile()
# try:
#   result = graph.invoke({"state": []})
#   print(result)
# except InvalidUpdateError as e:
#   print(f"An error ocurred: {e}")

# Now with a realist example

from langchain_core.documents import Document
from langchain.messages import HumanMessage, SystemMessage
from langchain_community.document_loaders import WikipediaLoader
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_tavily import TavilySearch

load_dotenv()


llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0)

class State(TypedDict):
  question: str
  answer: str
  context: Annotated[list, operator.add]

def search_web(state: State):
  """Retrieves docs from web search"""
  tavili_search = TavilySearchResults(max_results=3)
  search_docs = tavili_search.invoke(input=state["question"])
  formatted_search_docs = "\n\n---\n\n".join(
    [
      f'<Document href="{doc["url"]}"/>\n{doc["content"]}\n</Document>'
      for doc in search_docs
    ]
  )

  return {"context": [formatted_search_docs]}

def search_wikipedia(state: State):
  """Retrieves docs from wikipedia"""
  search_docs = WikipediaLoader(query=state["question"], load_max_docs=2).load()

  formatted_search_docs = "\n\n---\n\n".join(
    [
      f'<Document href="{doc.metadata["source"]}" page="{doc.metadata.get("page", "")}"/>\n{doc.page_content}\n</Document>'
      for doc in search_docs
    ]
  )

  return {"context": [formatted_search_docs]}

def generate_answer(state: State):
  """Node to answer a question"""
  context = state["context"]
  question = state["question"]

  answer_template = """Answer the question {question} using this context: {context}"""
  answer_instructions = answer_template.format(question=question, context=context)

  answer = llm.invoke([SystemMessage(content=answer_instructions)] + [HumanMessage(content=f"Answer the question.")])
  return {"answer": answer}

builder = StateGraph(State)

builder.add_node("search_web", search_web)
builder.add_node("search_wikipedia", search_wikipedia)
builder.add_node("generate_answer", generate_answer)

builder.add_edge(START, "search_web")
builder.add_edge(START, "search_wikipedia")
builder.add_edge(START, "generate_answer")
builder.add_edge("search_web", "generate_answer")
builder.add_edge("search_wikipedia", "generate_answer")
builder.add_edge("generate_answer", END)

graph = builder.compile()

response = graph.invoke({"question": "What are the expectations for NVidia Q2 2026 earnings?"})

print(response["answer"].content)