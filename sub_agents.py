from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent
from tools import search_web, search_cisco_docs
from dotenv import load_dotenv
from langchain_core.tools import tool
import os

agent_model = ChatAnthropic(
    model="claude-haiku-4-5",
    temperature=0
)

bgp_agent = create_agent(
    model = agent_model,
    tools=[search_cisco_docs, search_web],
    system_prompt= """You are a BGP specialist for Cisco routers. Your job is to help network engineers 
    troubleshoot and resolve BGP issues.

    You have deep knowledge of:
    - BGP neighbor states: Idle, Connect, Active, OpenSent, OpenConfirm, Established
    - eBGP and iBGP differences and configurations
    - BGP route advertisement, filtering and prefix lists
    - BGP attributes: AS-path, MED, Local Preference, Weight
    - Common BGP issues and how to resolve them
    - Cisco IOS/IOS-XE BGP commands

    When answering:
    - Always use search_cisco_docs first to find relevant documentation
    - Use search_web for recent issues or information not in the docs
    - Provide specific Cisco CLI commands when relevant
    - Be precise and technical
    - Structure your response with clear steps
    """
)

@tool
def run_bgp_agent(query: str):
    """Specialist for BGP troubleshooting on Cisco routers.
    Use this for ANY question about BGP neighbors, states, 
    route advertisement, filtering or BGP configuration issues."""
    
    result = bgp_agent.invoke({
        "messages": [{"role": "user", "content": query}]
    })
    return result["messages"][-1].content

upgrade_agent = create_agent(
    model = agent_model,
    tools=[search_cisco_docs, search_web],
    system_prompt="""You are a Cisco C8200/C8300 upgrade specialist. Your job is to help network engineers 
    plan and execute software upgrades on Cisco Catalyst 8200 and 8300 series routers.

    You have deep knowledge of:
    - Pre-upgrade checklist: disk space, current version, backup procedures
    - Upgrade procedures: install mode vs bundle mode
    - IOS XE upgrade commands and verification steps
    - Post-upgrade verification: interfaces, routing protocols, services
    - Rollback procedures in case of failure
    - Compatibility between IOS XE versions and hardware
    - Common upgrade issues and how to resolve them

    When answering:
    - Always use search_cisco_docs first to find relevant documentation
    - Use search_web for recent release notes or issues not in the docs
    - Provide specific CLI commands for each step
    - Always include pre and post upgrade verification steps
    - Be precise and warn about potential risks
    - Structure your response as a step-by-step procedure"""
)

@tool
def run_upgrade_agent(query: str):
    """Specialist for Cisco C8200/C8300 device upgrades and migrations.
    Use this for ANY question about upgrade procedures, software versions,
    IOS XE compatibility, pre/post upgrade verification, or rollback procedures."""

    result = upgrade_agent.invoke({"messages": [{"role":"user", "content":query}]})
    return result["messages"][-1].content


if __name__ == "__main__":
    print(run_bgp_agent.invoke("What are the BGP neighbor states?"))
    print(run_upgrade_agent.invoke("How to verify a successful upgrade on C8300?"))