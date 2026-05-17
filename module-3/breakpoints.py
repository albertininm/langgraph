from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

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

tools = [multiply, add, divide]

llm = ChatOpenAI(model="gpt-4.1-nano")
llm_with_tools = llm.bind_tools(tools)

from langchain.messages import SystemMessage, HumanMessage
from langgraph.graph import MessagesState, StateGraph, START
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.checkpoint.memory import MemorySaver
from pprint import pprint

system_message = SystemMessage(content="You are a helful assistant tasked with performing arithmetic on a set of inputs.")

# Node
def assistant(state: MessagesState):
  return {"messages": [llm_with_tools.invoke([system_message] + state["messages"])]}

builder = StateGraph(MessagesState)
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "assistant")
builder.add_conditional_edges(
  "assistant",
  tools_condition
)
builder.add_edge("tools", "assistant")

memory = MemorySaver()
react_graph = builder.compile(interrupt_before=["tools"],checkpointer=memory)
config = {"configurable": {"thread_id": 1}}

messages = [HumanMessage("Add 3 and 4. Multiply the output by 2. Divide the output by 5")]
# result = react_graph.invoke({"messages": messages}, config=config)
for event in react_graph.stream(input={"messages": messages}, config=config, stream_mode="values"):
  event["messages"][-1].pretty_print()

# Quando eu reexecuto o grafo passando None como input, ele executa de onde eu parei (que foi na chamada da tool multiply)
# for event in react_graph.stream(None, config=config, stream_mode="values"):
#   event["messages"][-1].pretty_print()

# Usando condicional para executar o codigo acima (para continuar a execucao)
user_approval = input("Do you want to call the tool? (yes/no):")

if user_approval == "yes":  
  for event in react_graph.stream(None, config=config, stream_mode="values"):
    event["messages"][-1].pretty_print()
else:
  print("operation canceled!")


# state = react_graph.get_state(config)
# state = react_graph.get_state_history(config)
# pprint(state)