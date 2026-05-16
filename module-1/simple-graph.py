from typing import TypedDict

# State
class MyState(TypedDict):
  graph_state: str

# Nodes
def node_1(state):
  print('----Node 1----')
  return {"graph_state": state['graph_state'] + ' I am'}

def node_2(state):
  print('----Node 2----')
  return {"graph_state": state['graph_state'] + ' happy!'}

def node_3(state):
  print('----Node 3----')
  return {"graph_state": state['graph_state'] + ' sad :('}

# Edges
import random
from typing import Literal

def decide_mood_node(state) -> Literal["node_2", "node_3"]:
  # Usually we use the state to decide which Node to go next
  user_input = state["graph_state"]

  if random.random() < 0.5:
    return "node_2"
  
  return "node_3"

from langgraph.graph import StateGraph, START, END

# Build graph
builder = StateGraph(MyState)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)

# Logic

builder.add_edge(START, "node_1")
builder.add_conditional_edges("node_1", decide_mood_node)
builder.add_edge("node_2", END)
builder.add_edge("node_3", END)

# Build graph
graph = builder.compile()

result = graph.invoke({"graph_state": "Hi, this is Albert"})

print(result)
