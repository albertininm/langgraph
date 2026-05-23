from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.messages import SystemMessage, HumanMessage
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.checkpoint.memory import MemorySaver
from pprint import pprint

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

system_message = SystemMessage(content="You are a helpful assistant tasked with performing arithmatic on a set of inputs.")

def assistant_node(state: MessagesState) -> MessagesState:
  return {"messages": [llm_with_tools.invoke([system_message] + state["messages"])]}

builder = StateGraph(MessagesState)

builder.add_node("assistant_node", assistant_node)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "assistant_node")
builder.add_conditional_edges("assistant_node", tools_condition)
builder.add_edge("tools", "assistant_node")

memory = MemorySaver()

graph = builder.compile(checkpointer=memory)


initial_input = {"messages": "Multiply 2 and 3"}
config = {"configurable": {"thread_id": 1}}

for event in graph.stream(initial_input, config=config, stream_mode="values"):
  event["messages"][-1].pretty_print()
# Prints the state at the current "snapshot"
# print(graph.get_state(config=config))

# We can see its previous states

all_states = [s for s in graph.get_state_history(config=config)]
# most recent state:
# print(all_states[0])
# oldest recent state:
# print(all_states[-2])

# Replay: quando passamos None, nós continuamos a execução de onde parou, mas se a gente passar um checkpoint_id
# junto com a config, podemos dar "replay" a partir do checkpoint em questao
# Replay é para Debugging em Human-in-the-loop cases:
# 1. Approval
# 2. Debugging
# 3. Editing
# to_replay = all_states[-2]
# print(to_replay.values)
# print(to_replay.next)
# print(to_replay.config)

# for event in graph.stream(None, config=to_replay.config, stream_mode="values"):
#   event["messages"][-1].pretty_print()

# Forking: já fizemos isso quando executamos graph.update_state, mas a gente sempre fez isso a partir do current state
# com a mesma ideia, se passarmos o checkpoint_id para a função update_state, criamos uma branch a partir daquele ponto, e não do current
to_fork = all_states[-2]

print(to_fork.values)
print(to_fork.config)

# IMPORTANT: porque nós queremos alterar a mensagem original, é importante passar o `id` da HumanMessage, caso contrário
# o add_message reducer do MessagesState iria adicionar 2 HumanMessage ao invés de alterar a existente do checkpoint na key "messages"
fork_config = graph.update_state(to_fork.config, {"messages": [HumanMessage(content="Multiply 5 and 3", id=to_fork.values["messages"][0].id)]})

print(fork_config)
for event in graph.stream(None, config=fork_config, stream_mode="values"):
  event["messages"][-1].pretty_print()

all_states = [s for s in graph.get_state_history(config=config)]
print(len(all_states))

print(all_states[0])