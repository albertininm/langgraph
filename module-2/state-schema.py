from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain.messages import HumanMessage, AIMessage
from langgraph.prebuilt import ToolNode, tool_validator
from langgraph.graph import StateGraph, START, END
from typing import Literal, TypedDict
from dataclasses import dataclass
import random
from typing import Literal

load_dotenv()

llm = ChatOpenAI(model="gpt-4.1-nano")

# Problem: using Typedict as a state schema may lead to run time issues as type validations won't be caught in run-time


class TypedDictState(TypedDict):
  name: str
  mood: Literal["happy", "sad"]


# def node_1(state):
#   print('----Node 1----')
#   return {"name": state["name"] + "is ... "}

# def node_2(state):
#   print('----Node 2----')
#   return {"mood": "happy"}

# def node_3(state):
#   print('----Node 3----')
#   return {"mood": "sad"}



# def decide_mood_node(state) -> Literal["node_2", "node_3"]:
#   # Usually we use the state to decide which Node to go next
#   if random.random() < 0.5:
#     return "node_2"
  
#   return "node_3"

# Build graph
# builder = StateGraph(TypedDictState)
# builder.add_node("node_1", node_1)
# builder.add_node("node_2", node_2)
# builder.add_node("node_3", node_3)

# builder.add_edge(START, "node_1")
# builder.add_conditional_edges("node_1", decide_mood_node)
# builder.add_edge("node_2", END)
# builder.add_edge("node_3", END)

# graph = builder.compile()

# response = graph.invoke({"name": "Albert"})

# print(response)

# -------------
# Now, using dataclass for defining a Class to act as state

# @dataclass
# class DataClassState:
#   name: str
#   mood: Literal["happy", "sad"]

def node_1(state):
  print('----Node 1----')
  return {"name": state.name + " is ... ", "mood": state.mood}

def node_2(state):
  print('----Node 2----')
  return {"mood": "happy"}

def node_3(state):
  print('----Node 3----')
  return {"mood": "sad"}

def decide_mood_node(state) -> Literal["node_2", "node_3"]:
  # Usually we use the state to decide which Node to go next
  if random.random() < 0.5:
    return "node_2"
  
  return "node_3"

# builder = StateGraph(DataClassState)
# builder.add_node("node_1", node_1)
# builder.add_node("node_2", node_2)
# builder.add_node("node_3", node_3)

# builder.add_edge(START, "node_1")
# builder.add_conditional_edges("node_1", decide_mood_node)
# builder.add_edge("node_2", END)
# builder.add_edge("node_3", END)

# graph = builder.compile()

# # Issue in runtime
# response = graph.invoke(DataClassState(name="Albert", mood="mad"))
# print(response)

# Pydantic is the solution for typing it provides data validation

from pydantic import BaseModel, field_validator, ValidationError

class PydanticState(BaseModel):
  name: str
  mood: Literal["happy", "sad"]

  @field_validator("mood")
  @classmethod
  def validate_mood(cls, value, info):
    # print(info)
    if value not in ["happy", "sad"]:
      raise ValueError("Each mood must be either 'happy' or 'sad'")
    return value

try:
  state = PydanticState(name="Albert", mood="happy")
except ValidationError as e:
  print("Validation Error:", e)

builder = StateGraph(PydanticState)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)

builder.add_edge(START, "node_1")
builder.add_conditional_edges("node_1", decide_mood_node)
builder.add_edge("node_2", END)
builder.add_edge("node_3", END)

graph = builder.compile()
response = graph.invoke(PydanticState(name="Albert", mood="sad"))
print(response)

# So, Pydentic is helpful if we want to apply validation in any of our state fields