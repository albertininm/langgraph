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

react_graph = builder.compile()

messages = [HumanMessage("Add 3 and 4. Multiply the output by 2. Divide the output by 5")]
result = react_graph.invoke({"messages": messages})
for m in result["messages"]:
  m.pretty_print()