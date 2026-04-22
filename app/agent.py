from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
from langchain.messages import ToolMessage 
from typing import Literal
from app.tools import search_cisco_vuln, search_web
from app.sub_agents import run_bgp_agent, run_upgrade_agent
from langgraph.checkpoint.sqlite import SqliteSaver
from pathlib import Path
import os, sqlite3

#Loading my keys
load_dotenv()
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
and general network problems. Be precise, technical, and provide step-by-step guidance.

IMPORTANT - You have access to the following tools and MUST use the tools when the query asks something related 
to the tools:
- run_bgp_agent: Use for questions about BGP, BGP down, issues with BGP flapping or other related issues to BGP
- search_web: Use for recent information not covered by the docs
- search_cisco_vuln: Use for questions about CISCO CVEs or security vulnerabilities
- run_upgrade_agent: Use for questions and information required about Catalyst 8200 and 8300 (C8200/8300) CISCO devices upgrades.

Always prefer using tools when the question is related to their scope.
If no tool is relevant, answer from your knowledge."""

#tools
tools = [search_web, run_upgrade_agent, run_bgp_agent, search_cisco_vuln]
model_with_tools = model.bind_tools(tools)
tools_by_name = {tool.name: tool for tool in tools}

#LLM node
def LLM_node(state: MessagesState) -> dict:
    system_message = SystemMessage(content = System_prompt)
    messages = [system_message] + state["messages"]
    response = model_with_tools.invoke(messages)
    return{
        "messages": [response]
    }

#Tool node
def tool_node(state: MessagesState) -> dict:
    "Performs the tools calling when required"
    
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}

#router edge -- ReAct
def router_edge(state: MessagesState) -> Literal["tool_node", END]:
    "Decides if we should continue the loop or stop based upon whether the LLM made a tool call"

    messages = state["messages"]
    if messages[-1].tool_calls:
        return "tool_node"
    
    return END

#building my agent
agent_builder = StateGraph(MessagesState)
agent_builder.add_node("llm_node", LLM_node)
agent_builder.add_node("tool_node",tool_node)

agent_builder.add_edge(START, "llm_node")
agent_builder.add_conditional_edges(
    "llm_node",
    router_edge,
    ["tool_node", END]
)
agent_builder.add_edge("tool_node", "llm_node")

MEMORY_BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(MEMORY_BASE_DIR / "data" / "memory.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
memory = SqliteSaver(conn)
agent = agent_builder.compile(checkpointer=memory)

with open("graph.png", "wb") as f:
    f.write(agent.get_graph().draw_mermaid_png())

def chat(message: str, thread_id: str):
    config = {"configurable":{"thread_id":thread_id}}
    response = agent.invoke({"messages":[HumanMessage(content=message)]}, config=config)
    return({
        "diagnosis":response["messages"][-1].content,
        "session_id":thread_id
    })

if __name__ == "__main__":
    thread_id = "tools_test"
    while True:
        message = input("You: ")
        
        if message.lower() in ["exit", "quit"]:
            break
        
        chat(message, thread_id)