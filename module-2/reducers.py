from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# class State(TypedDict):
#   foo: int

# def node_1(state):
#   print("----Node 1-----")
#   return {"foo": state["foo"] + 1}

# def node_2(state):
#   print("----Node 2-----")
#   return {"foo": state["foo"] + 1}

# def node_3(state):
#   print("----Node 3-----")
#   return {"foo": state["foo"] + 1}

# builder = StateGraph(State)
# builder.add_node("node_1", node_1)
# builder.add_node("node_2", node_2)
# builder.add_node("node_3", node_3)
# builder .add_edge(START, "node_1")
# builder .add_edge("node_1", "node_2")
# builder .add_edge("node_1", "node_3")
# builder .add_edge("node_2", END)
# builder .add_edge("node_3", END)

# graph = builder.compile()

# response = graph.invoke({"foo": 0})
# print(response)
# ERROR because we're trying to update the same state key in the same step in 2 different nodes.
#  ------------------
# To solve this we should create a REDUCER function (add) and pass it to our Annotated class prop
from typing import Annotated
from operator import add

class State(TypedDict):
  foo: Annotated[list[int], add]

def node_1(state):
  print("----Node 1-----")
  return {"foo": [state["foo"][0] + 1]}

def node_2(state):
  print("----Node 2-----")
  return {"foo": [state["foo"][-1] + 1]}

def node_3(state):
  print("----Node 3-----")
  return {"foo": [state["foo"][-1] + 1]}

builder = StateGraph(State)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)
builder .add_edge(START, "node_1")
builder .add_edge("node_1", "node_2")
builder .add_edge("node_1", "node_3")
builder .add_edge("node_2", END)
builder .add_edge("node_3", END)

graph = builder.compile()
# No more errors
# response = graph.invoke({"foo": [1]})
# print(response)

# Now testing there's an issue here if we pass None as value
# try:
#   response = graph.invoke({"foo": None})
# except TypeError as e:
#   print(f"TypeError occurred: {e}")

# print(response)

# In this case, we create a custom reducer
def reduce_list(left: list | None, right: list | None) -> list:
  """Safely combine two lists, handling cases where either or both inputs might be None
  
  Args:
    left (list | None): The first list to combine, or None
    right (list | None): The second list to combine, or None
  
  Returns:
    list: A new list containing all elements from both input lists.
          If an input is None, it's treated as an empty list.
  """

  if not left:
    left = []

  if not right:
    right = []

  return left + right

class CustomReducerState(TypedDict):
  foo: Annotated[list[int], reduce_list]

builder = StateGraph(CustomReducerState)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)
builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")
builder.add_edge("node_1", "node_3")
builder.add_edge("node_2", END)
builder.add_edge("node_3", END)

# graph = builder.compile()

# try:
#   response = graph.invoke({"foo": None})
#   print(response)
# except TypeError as e:
#   print(f"TypeError occurred: {e}")


from langchain.messages import AnyMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages, MessagesState

# Defining a custom state with TypedDict that includes a list of messages with add_messages reducer
class CustomMessagesState(TypedDict):
  messages: Annotated[list[AnyMessage], add_messages]
  added_key_1: str
  added_key_2: str

# We can also use MessagesState, which includes the messages key with add_messages reducer
class ExtendedMessagesState(MessagesState):
  added_key_1: str
  added_key_2: str

# Let's talk a little bit more about add_messages reducer

initial_messages = [
  AIMessage(content="Hello! How can I assist you?", name="Model", id=1),
  HumanMessage(content="I'm looking for information on marine biology.", name="Albert", id=2)
]

# Adding
# new_message = AIMessage(content="Sure, I can help with that. What specifically are you interested in?", name="Model", id=3)

# Rewriting
# When we add IDs to our messages, if we add a message with the same ID that is already in the list it overrides the content of the one in the list
# new_message = AIMessage(content="Sure, I can help with that. What specifically are you interested in?", name="Model", id=2)

# print(add_messages(initial_messages, new_message))

# Removal.
from langchain_core.messages import RemoveMessage

messages = [AIMessage("Hi", name="Bot", id=1)]
messages.append(HumanMessage("Hi", name="Albert", id=2))
messages.append(AIMessage("So you said you were researching ocean mammals?", name="bot", id=3))
messages.append(HumanMessage("Yes, I know about whales. But what others should I learn about?", name="Albert", id=4))

delete_messages_reducer = [RemoveMessage(id=m.id) for m in messages[:2]]
# print(delete_messages_reducer)
print(add_messages(messages, delete_messages_reducer))