
from langchain.messages import HumanMessage, AIMessage, RemoveMessage
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from pprint import pprint
from langgraph.graph import MessagesState, StateGraph, START, END
from langchain.messages import trim_messages
from langchain_openai import ChatOpenAI

load_dotenv()


messages = [AIMessage(f"So you said you were researching ocean mammals?", name="Bot")]
messages.append(HumanMessage(f"Yes, I know about whales. But what others should I learn about?", name="Albert"))

# for m in messages:
#   m.pretty_print()

model = init_chat_model(model="gpt-4.1-nano", model_provider="OpenAI", temperature=0.1, max_tokens=2048)

# response = model.invoke(messages)

# pprint(response)

def chat_model_node(state: MessagesState):
  return {"messages": model.invoke(state["messages"])}

builder = StateGraph(MessagesState)
# builder.add_node("chat_model_node", chat_model_node)
# builder.add_edge(START, "chat_model_node")
# builder.add_edge("chat_model_node", END)

# graph = builder.compile()

# response = graph.invoke({"messages": messages})
# pprint(response)

# As the conversation grows, the number of messages increase and we can remove them automatically
# as the MessagesState user the add_messages reducer automatically, we add RemoveMessage with the ids we want to remove

def filter_messages(state: MessagesState):
  messages_to_delete = [RemoveMessage(id = m.id) for m in state["messages"][:-2]]
  return {"messages": messages_to_delete}

builder = StateGraph(MessagesState)
builder.add_node("filter_messages", filter_messages)
builder.add_node("chat_model_node", chat_model_node)

builder.add_edge(START, "filter_messages")
builder.add_edge("filter_messages", "chat_model_node")
builder.add_edge("chat_model_node", END)


graph = builder.compile()

messages = [AIMessage("Hi", name="Bot", id=1)]
messages.append(HumanMessage("Hi", name="Albert", id=2))
messages.append(AIMessage("How can I help you today?", name="Bot", id=3))
messages.append(HumanMessage("I need your help with something because today I woke up very lazy and I couldn't work as much as I wanted", name="Albert", id=4))

# response = graph.invoke({"messages": messages})
# pprint(response)

# We can also modify the chat node to only pass to the LLM the most recent message (no history) and keep state intact
# def chat_model_node(state: MessagesState):
#   return {"messages": model.invoke([state["messages"][:-1]])}

# We can also use trim_messages

def chat_model_node(state: MessagesState):
  messages = trim_messages(
    state["messages"],
    max_tokens=100,
    strategy="last",
    token_counter=ChatOpenAI(model="gpt-4.1-nano"),
    allow_partial=False
    # allow_partial=False only gets the last message
  )
  return {"messages": model.invoke(messages)}

builder = StateGraph(MessagesState)
builder.add_node("chat_model_node", chat_model_node)
builder.add_edge(START, "chat_model_node")
builder.add_edge("chat_model_node", END)

graph = builder.compile()

response = graph.invoke({"messages": messages})
pprint(response)