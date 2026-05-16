from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.messages import SystemMessage, HumanMessage, RemoveMessage, AIMessage
from pprint import pprint
load_dotenv()

model = ChatOpenAI(model="gpt-4.1-nano")

class State(MessagesState):
  summary: str

def call_model_node(state: State):
  summary = state.get("summary", "")

  if summary:
    system_message = f"Summary of conversation earlier: {summary}"
    messages = [SystemMessage(content=system_message) + state["messages"]]
  else:
    messages = state["messages"]

  return {"messages": model.invoke(messages)}

def summarize_conversation(state: State):
  summary = state.get("summary", "")

  if summary:
    summary_message = (
      f"This is summary of the conversation to date: {summary}\n\n"
      "Extend the summary by taking into account the new messages above:"
    )
  else:
    summary_message = "Create a summary of the conversation above:"

  # ADd prompt to our history. At this point, we're telling the LLM to create a summary of what came before
  messages = state["messages"] + [HumanMessage(content=summary_message)]
  # This is the summary
  summary = model.invoke(messages)

  # Now that we have a summary, we can delete old messages
  messages_to_delete = [RemoveMessage(id = m.id) for m in state["messages"][:-2]]

  return {"summary": summary.content, "messages": messages_to_delete}

# Decides whether to end or summarize the conversation
def should_continue_node(state: State):
  messages = state["messages"]

  if len(messages) > 5:
    return "summarize_conversation"
  
  return END

builder = StateGraph(State)
builder.add_node("call_model_node", call_model_node)
builder.add_node("summarize_conversation", summarize_conversation)

builder.add_edge(START, "call_model_node")
builder.add_conditional_edges("call_model_node", should_continue_node)
builder.add_edge("summarize_conversation", END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": 1}}

response = graph.invoke({"messages": [
  AIMessage("Hi", name="Bot", id=1),
  HumanMessage("Hello", name="Albert", id=2),
  AIMessage("How can I assist you today?", name="Bot", id=3),
  HumanMessage("I need you to cook pizza for me today", name="Albert", id=4),
]}, config=config)

for message in response["messages"]:
  message.pretty_print()

response = graph.invoke({"messages": [AIMessage("Of course! I am a pizza specialist, just plug your electic oven and I can do it for you!", name="Bot", id=5)]}, config=config)

print("\n\n\n")
pprint(response)