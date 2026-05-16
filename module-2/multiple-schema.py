# Motivation: Typically the Graph's state is one for the entire graph, but sometimes we need some data in a state between nodes
# that is not needed/relevant for the input/output

# Private State
# Useful for anything needed as part of the intermediate working logic of the Graph
# Not relevant for the overall Graph

from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# class OverallState(TypedDict):
#   foo: int

# class PrivateState(TypedDict):
#   baz: int

# def node_1(state: OverallState) -> PrivateState:
#   print("----Node 1----")
#   return {"baz": state['foo'] + 1}

# def node_2(state: PrivateState) -> OverallState:
#   print("----Node 2----")
#   return {"foo": state['baz'] + 1}

# builder = StateGraph(OverallState)
# builder.add_node("node_1", node_1)
# builder.add_node("node_2", node_2)

# builder.add_edge(START, "node_1")
# builder.add_edge("node_1", "node_2")
# builder.add_edge("node_2", END)

# graph = builder.compile()

# response = graph.invoke({"foo": 1})
# print(response)

# StateGraph, by default, takes in a single schema and all nodes are expected to communicate with that schema
# However it's possible to define explicit input and output schemas for a graph.
# Defining an "internal" schema that contains all keys relevant to graph operations
# But we use specific input and output schemas to constrain the input and output

class OverallState(TypedDict):
  question: str
  answer: str
  notes: str

def thinking_node(state: OverallState):
  return {"answer": "bye", "notes": "... his is name is Lance"}

def answer_node(state: OverallState):
  return {"answer": "bye Lance"}

builder = StateGraph(OverallState)
builder.add_node("answer_node", answer_node)
builder.add_node("thinking_node", thinking_node)
builder.add_edge(START, "thinking_node")
builder.add_edge("thinking_node", "answer_node")
builder.add_edge("answer_node", END)

graph = builder.compile()

# At this point, the state returns {'question': 'hi', 'answer': 'bye Lance', 'notes': '... his is name is Lance'}
# So, every return of a Node overwrites a specific key in the state
# response = graph.invoke({"question": "hi"})
# print(response)

# If we want to have a few keys for input/output, we can define input and output schemas
# When I return the output schema, the state that is returned only returns the keys that are defined in the output schema

class InputState(TypedDict):
  question: str

class OutputState(TypedDict):
  answer: str

class OverallState(TypedDict):
  question: str
  answer: str
  notes: str


def thinking_node(state: InputState):
  return {"answer": "bye", "notes": "... his is name is Lance"}

# Because of the type definition, the key filter is applied
def answer_node(state: OverallState) -> OutputState:
  return {"answer": "bye Lance"}

# Applying input/output filters
builder = StateGraph(OverallState, input=InputState, output=OutputState)
builder.add_node("answer_node", answer_node)
builder.add_node("thinking_node", thinking_node)
builder.add_edge(START, "thinking_node")
builder.add_edge("thinking_node", "answer_node")
builder.add_edge("answer_node", END)

graph = builder.compile()
response = graph.invoke({"question": "hi"})
print(response)
