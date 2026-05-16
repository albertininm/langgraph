from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, AIMessage
from pprint import pprint
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

messages = [
  HumanMessage(content="what's 5 times 4?"),
]

# model = init_chat_model(
#   model="gemma4:26b",
#   model_provider="ollama",
#   base_url="http://localhost:11434/",
#   max_tokens=4096,
#   temperature=1.0
# )

model = ChatOpenAI(name="gpt-4.1-nano")

def multiply(a: int, b:int) -> int:
  """Multiply a and b

  Args:
    a: first int
    b: second int
  """

  return a * b

llm_with_tools = model.bind_tools([multiply])

result = llm_with_tools.invoke(messages)

pprint(result)