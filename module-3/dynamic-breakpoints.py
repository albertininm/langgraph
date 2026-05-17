from dotenv import load_dotenv
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import NodeInterrupt

load_dotenv()

class State(TypedDict):
  input: str

def node_1(state: State) -> State:
  print("---Node 1---")
  return state

def node_2(state: State) -> State:
  if len(state["input"]) > 5:
    raise NodeInterrupt(f"Received input that is longer than 5 characters: {state['input']}")

  print("---Node 2---")
  return state

def node_3(state: State) -> State:
  print("---Node 3---")
  return state

builder = StateGraph(State)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)

builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")
builder.add_edge("node_2", "node_3")
builder.add_edge("node_3", END)

memory = MemorySaver()

graph = builder.compile(checkpointer=memory)

initial_input = {"input": "hello world"}
thread_config = {"configurable": {"thread_id": 1}}

for event in graph.stream(initial_input, thread_config, stream_mode="values"):
  print(event)

state = graph.get_state(thread_config)
print(state.next)
print(state.tasks)

# Nothing happens because we didn't update the state
for event in graph.stream(None, thread_config, stream_mode="values"):
  print(event)

# Now we update the state and see
graph.update_state(thread_config, {"input": "hi"})

state = graph.get_state(thread_config)
print(state.next)

for event in graph.stream(None, thread_config, stream_mode="values"):
  print(event)