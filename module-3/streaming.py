# Chatbot

from langchain_openai import ChatOpenAI
from langchain.messages import AIMessage, HumanMessage, SystemMessage, RemoveMessage
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver
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

graph = builder.compile(checkpointer=MemorySaver())

config = {"configurable": {"thread_id": 1}}

# for chunk in graph.stream({"messages": [
#   HumanMessage("Hello, my name is Albert and I like cheese", name="Albert", id=1),
# ]}, config=config, stream_mode="updates"):
#   pprint(chunk)

# stream_mode="updates" mostra apenas o que foi mudado no nó atual (ao final da execução do nó)
# for chunk in graph.stream({"messages": [
#   HumanMessage("Hello, my name is Albert and I like cheese", name="Albert", id=1),
# ]}, config=config, stream_mode="updates"):
#   chunk["model_node"]["messages"].pretty_print()

config = {"configurable": {"thread_id": 2}}

# stream_mode="values" faz streaming do estado inteiro toda vez que um nó do grafo execute 
# for event in graph.stream({"messages": [
#   HumanMessage("Hello, my name is Albert and I like cheese", name="Albert", id=1),
# ]}, config=config, stream_mode="values"):
#   for m in event["messages"]:
#     m.pretty_print()

# graph_state = graph.get_state(config)
# pprint(graph_state)

# Streaming tokens de um LLM que esteja no Grafo como um nó

# async def main():
#   config = {"configurable": {"thread_id": 3}}

#   input_message = HumanMessage(content="Tell me about the 49ers NFL team")


#   # THis shows a lot of events 
#   # async for event in graph.astream_events({"messages": [input_message]}, config=config, version="v2"):
#   #   print(f"Node: {event['metadata'].get("langgraph_node", "")} Type: {event['event']} Name: {event['name']}")

#   # Let's filter events by type for a specific node
#   node_to_stream = "model_node"
#   async for event in graph.astream_events({"messages": [input_message]}, config=config, version="v2"):
#     if event["event"] == "on_chat_model_stream" and event["metadata"].get("langgraph_node", "") == node_to_stream:
#       print(event["data"]["chunk"].content, end="|")


# if __name__ == "__main__":
#   import asyncio
#   asyncio.run(main())

# Exploring the stream mode "messages"

async def main():
  config = {"configurable": {"thread_id": 3}}

  input_message = HumanMessage(content="Tell me about the 49ers NFL team")


  # THis shows a lot of events 
  # async for event in graph.astream_events({"messages": [input_message]}, config=config, version="v2"):
  #   print(f"Node: {event['metadata'].get("langgraph_node", "")} Type: {event['event']} Name: {event['name']}")

  # Let's filter events by type
  node_to_stream = "model_node"
  for message, metadata in graph.stream({"messages": [input_message]}, config=config, stream_mode="messages"):
      # print(metadata)
    if metadata["langgraph_node"] == node_to_stream:
      print(message.content, end="")


if __name__ == "__main__":
  import asyncio
  asyncio.run(main())