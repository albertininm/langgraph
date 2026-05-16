from typing import TypedDict, Annotated
from langchain.messages import AnyMessage, AIMessage, HumanMessage
from langgraph.graph.message import add_messages
from pprint import pprint
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv()

class MessagesState(MessagesState):
  pass

model = ChatOpenAI(name="gpt-4.1-nano")

def multiply(a: int, b:int) -> int:
  """Multiply a and b

  Args:
    a: first int
    b: second int
  """

  return a * b

llm_with_tools = model.bind_tools([multiply])

def tool_calling_llm(state: MessagesState):
  return {"messages": [llm_with_tools.invoke(state["messages"])]}

# def tools_condition(state: MessagesState):
#   # we could manually implement the logic here but there is a prebuilt tools_condition

  

builder = StateGraph(MessagesState)
builder.add_node("tool_calling_llm", tool_calling_llm)
builder.add_node("tools", ToolNode([multiply]))
builder.add_edge(START, "tool_calling_llm")
builder.add_conditional_edges(
  "tool_calling_llm",
  # If last message (result) from assistant is a tool call -> routes to tools
  # If last message (result) from assistant is NOT a tool call -> routes to END
  tools_condition
)

graph = builder.compile()

result = graph.invoke({
  "messages": [HumanMessage(content="Hello!")]
})

pprint(result)

result = graph.invoke({
  "messages": [HumanMessage(content="Multiply 2 and 3")]
})

for m in result["messages"]:
  m.pretty_print()