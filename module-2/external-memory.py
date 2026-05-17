import sqlite3
import os 
from pathlib import Path

# ----------- Database setup -------------------
# It will creates an in-memory SQLite database just as MemorySaver
# conn = sqlite3.connect(":memory:")


db_path = "state_db/example.db"
# Extract the directory from your db_path
db_dir = Path(db_path).parent

# Create the folder and any missing parent directories
db_dir.mkdir(parents=True, exist_ok=True)

# If we suply a db_path, it creates a database for us!
conn = sqlite3.connect(db_path, check_same_thread=False)

from langgraph.checkpoint.sqlite import SqliteSaver

memory = SqliteSaver(conn)


# Chatbot

from langchain_openai import ChatOpenAI
from langchain.messages import AIMessage, HumanMessage, SystemMessage, RemoveMessage
from langgraph.graph import START, END, StateGraph, MessagesState
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

model = ChatOpenAI(model="gpt-4.1-nano", temperature=0)

class State(MessagesState):
  summary: str


def model_node(state: State):
  summary = state.get("summary", "")

  # If there's a summary, we add it
  if summary:
    # Add summary to system message
    system_message = f"Summary of conversation earlier: {summary}"
    messages = [SystemMessage(content=system_message)] + state["messages"]
  else:
    messages = state["messages"]

  response = model.invoke(messages)
  return {"messages": response}

def summarize_conversation(state: State):
  # First we get any existing summary
  summary = state.get("summary")
  if summary:
    summary_prompt = (
      f"This is the summary of the conversation to date: {summary}"
      "Extend the summary by taking into account the new messages above:"
    )
  else:
    summary_prompt = "Create a summary of the conversation above:"
  
  # Then we generate a summary to add to the state
  messages = state["messages"] + [HumanMessage(content=summary_prompt)]
  response = model.invoke(messages)

  # From the list of messages, we delete everything but the latest 2
  # as we have a summary in the other state property
  messages_to_delete = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
  return {"summary": response.content, "messages": messages_to_delete}

def decide_summarize(state: State):
  messages = state["messages"]

  if len(messages) > 6:
    return "summarize_conversation"
  
  return END

builder = StateGraph(State)
builder.add_node("summarize_conversation", summarize_conversation)
builder.add_node("model_node", model_node)

builder.add_edge(START, "model_node")
builder.add_conditional_edges("model_node", decide_summarize)
builder.add_edge("summarize_conversation", END)

graph = builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": 1}}

# graph.invoke({"messages": [
#   HumanMessage("Hello, my name is Albert and I like cheese", name="Albert", id=1),
#   AIMessage("Hello Albert, how can I help you?", name="Bot", id=2),
# ]}, config=config)
graph.invoke({"messages": [
  HumanMessage("What do I like?", name="Albert", id=3),
]}, config=config)

graph_state = graph.get_state(config)
pprint(graph_state)