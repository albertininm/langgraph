from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

def multiply(a: int, b: int) -> int:
  """
    Multiply a and b.

    Args:
      a: first int
      b: second int
  """
  return a * b

def add(a: int, b: int) -> int:
  """
    Add a and b.

    Args:
      a: first int
      b: second int
  """
  return a + b

def divide(a: int, b: int) -> int:
  """
    Divide a and b.

    Args:
      a: first int
      b: second int
  """
  return a / b

tools = [multiply, add, divide]

llm = ChatOpenAI(model="gpt-4.1-nano")
llm_with_tools = llm.bind_tools(tools)

from langchain.messages import SystemMessage, HumanMessage
from langgraph.graph import MessagesState, StateGraph, START
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.checkpoint.memory import MemorySaver
from pprint import pprint

system_message = SystemMessage(content="You are a helful assistant tasked with performing arithmetic on a set of inputs.")

# Node
def assistant(state: MessagesState):
  return {"messages": [llm_with_tools.invoke([system_message] + state["messages"])]}

builder = StateGraph(MessagesState)
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "assistant")
builder.add_conditional_edges(
  "assistant",
  tools_condition
)
builder.add_edge("tools", "assistant")

memory = MemorySaver()
react_graph = builder.compile(interrupt_before=["assistant"],checkpointer=memory)
config = {"configurable": {"thread_id": 1}}

messages = [HumanMessage("Multiply 2 and 3")]
for event in react_graph.stream(input={"messages": messages}, config=config, stream_mode="values"):
  event["messages"][-1].pretty_print()

state=react_graph.get_state(config)
# pprint(state)

# Apply state update
react_graph.update_state(config, {"messages": HumanMessage("No, actually multiply 3 and 3!")})
state=react_graph.get_state(config)
pprint(state)

for event in react_graph.stream(None, config=config, stream_mode="values"):
  event["messages"][-1].pretty_print()

# Depois que a tool retornou o resultado, precisamos permitir o LLM responder novamente
for event in react_graph.stream(None, config=config, stream_mode="values"):
  event["messages"][-1].pretty_print()
