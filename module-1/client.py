from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode
from langchain.messages import SystemMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

def multiply(a: int, b: int) -> int:
  """
    Multiply a and b.

    Args:
      a: first int
      b: second int
  """
  return a * b

def add(a: int, b: int) -> int:
  """
    Add a and b.

    Args:
      a: first int
      b: second int
  """
  return a + b

def divide(a: int, b: int) -> int:
  """
    Divide a and b.

    Args:
      a: first int
      b: second int
  """
  return a / b

system_message = SystemMessage(content="You are a helpful assistant tasked with performing arithmetic on a set of inputs")

def assistant(state: MessagesState):
  return {"messages": llm_with_tools.invoke([system_message] + state["messages"])}


tools = [multiply, add, divide]
llm = ChatOpenAI(model="gpt-4.1-nano")
llm_with_tools = llm.bind_tools(tools)


builder = StateGraph(MessagesState)
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "assistant")
builder.add_conditional_edges(
  "assistant",
  tools_condition
)

builder.add_edge("tools", "assistant")

graph = builder.compile()

# result = graph.invoke({"messages": [HumanMessage("Add 3 and 4.")]})
# for m in result["messages"]:
#   m.pretty_print()

# # Problem! It doesn't remember the past invocation
# result = graph.invoke({"messages": [HumanMessage("Multiply that by 2")]})
# for m in result["messages"]:
#   m.pretty_print()

# Solution: memory!

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

# config = {"configurable": {"thread_id": 1}}

# result = graph.invoke({"messages": [HumanMessage("Add 3 and 4.")]}, config = config)
# for m in result["messages"]:
#   m.pretty_print()

# # Problem! It doesn't remember the past invocation
# result = graph.invoke({"messages": [HumanMessage("Multiply that by 2")]}, config = config)
# for m in result["messages"]:
#   m.pretty_print()


from langgraph_sdk import get_client
from pprint import pprint


async def main():
  URL = "http://127.0.0.1:2024"
  client = get_client(url=URL)

  assistants = await client.assistants.search()
  pprint(assistants)

  agent = assistants[1]
  thread = await client.threads.create()

  messages = {"messages": [HumanMessage(content="Multiply 3 by 2")]}

  async for chunk in client.runs.stream(
    thread["thread_id"],
    agent["assistant_id"],
    input=messages,
    stream_mode="values"
  ):
    if chunk.data and chunk.event != "metadata":
      print(chunk.data["messages"][-1])



if __name__ == "__main__":
  import asyncio
  asyncio.run(main())