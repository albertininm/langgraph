from typing import TypedDict, Annotated
from langchain.messages import AnyMessage, AIMessage, HumanMessage
from langgraph.graph.message import add_messages
from pprint import pprint
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# class MessagesState(TypedDict):
#   messages: list[AnyMessage]

# We can automatically append to the list by doing this:

# class MessagesState(TypedDict):
#   messages: Annotated[list[AnyMessage], add_messages]

# Since having a lista of messages in your state is so common, LangGraph has a pre-built `MessagesState`
# from langgraph.graph import MessagesState

# class State(MessagesState):
#   # Add any additional key beyond messages
#   pass


# Testing the reducer (add_messages)

# initial_messages = [
#   AIMessage(content="Hello! How can I assist you?", name="Model"),
#   HumanMessage(content="I'm looking for information on marine biology", name="Lance")
# ]

# new_message = AIMessage(content="Sure, I can help with that. What specifically are you interested in?", name="Model")

# result = add_messages(initial_messages, new_message)
# pprint(result)


# Full example
from langgraph.graph import MessagesState, StateGraph, START, END

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

builder = StateGraph(MessagesState)
builder.add_node("tool_calling_llm", tool_calling_llm)
builder.add_edge(START, "tool_calling_llm")
builder.add_edge("tool_calling_llm", END)

graph = builder.compile()

result = graph.invoke({
  "messages": [HumanMessage(content="Hello!")]
})

pprint(result)

result = graph.invoke({
  "messages": [HumanMessage(content="Multiply 2 and 3")]
})
pprint(result)