from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
import os

#Loading my keys
load_dotenv(".env")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
langsmith_key = os.getenv("LANGSMITH_API_KEY")

#Creating my model
model = ChatAnthropic(
    model="claude-haiku-4-5",
    temperature=0
)

#System prompt for my agent
System_prompt = """You are an expert network troubleshooting assistant specialized in Cisco devices. 
You help network engineers diagnose and resolve issues with BGP, device upgrades, 
and general network problems. Be precise, technical, and provide step-by-step guidance."""

#LLM node
def LLM_node(state: MessagesState) -> dict:
    system_message = SystemMessage(content = System_prompt)
    messages = [system_message] + state["messages"]
    response = model.invoke(messages)
    return{
        "messages": [response]
    }

#building my agent
agent_builder = StateGraph(MessagesState)
agent_builder.add_node("llm_node", LLM_node)
agent_builder.add_edge(START, "llm_node")
agent_builder.add_edge("llm_node", END)
memory = MemorySaver()
agent = agent_builder.compile(checkpointer=memory)

def chat(message: str, thread_id: str):
    config = {"configurable":{"thread_id":thread_id}}
    response = agent.invoke({"messages":[HumanMessage(content=message)]}, config=config)
    print(response["messages"])

with open("graph.png", "wb") as f:
    f.write(agent.get_graph().draw_mermaid_png())