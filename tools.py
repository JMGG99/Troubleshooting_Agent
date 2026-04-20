from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from rag import get_retriever
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import requests, os

@tool
def search_cisco_docs(query: str):
    """
    Use this tool to search Cisco documentation and internal PDFs for troubleshooting information.

    Use it when the user asks about:
    - BGP issues (neighbor down, flapping, etc.)
    - Cisco router configuration for software upgredes (C8200, C8300, etc.)
    - Software upgrades or compatibility

    Input: a natural language query
    Output: relevant documentation including sources
    """

    retriever = get_retriever()
    docs = retriever.invoke(query)

    if not docs:
        return "No relevant Cisco documentation found"
    
    results = []

    for i, doc in enumerate(docs, start=1):
        content = doc.page_content.strip()
        source = doc.metadata.get("source", "Unknown Source")

        formatted_text = f"""
        [Document {i}]
        Source: 
        {source}
        Content: 
        {content}
        """

        results.append(formatted_text)

    return "\n".join(results)

@tool
def search_web(query: str):
    """
    Use this tool to search the web for recent or external information.

    Use it when:
    - The question involves recent events or updates
    - Looking for CVEs or vulnerabilities not found in internal docs
    - The RAG system does not return sufficient information
    - General networking topics not covered in Cisco PDFs

    Input: a natural language query
    Output: summarized web search results
    """

    result = DuckDuckGoSearchRun().run(query)
    return result

@tool
def search_cisco_vuln(cve_id: str):
    """Search for Cisco security vulnerabilities and advisories by CVE ID.
    Use this tool when the user asks about a specific CVE, security vulnerability,
    or wants to know if a Cisco device is affected by a known security issue.
    """

    token_url = "https://id.cisco.com/oauth2/default/v1/token"

    token_response = requests.post(
        token_url,
        data = {"grant_type": "client_credentials"},
        auth = (
            os.getenv("CISCO_CLIENT_ID"),
            os.getenv("CISCO_CLIENT_SECRET")
        )
    )

    if token_response.status_code != 200:
        return f"Error obteniendo token: {token_response.status_code}"
    
    token = token_response.json()["access_token"]

    api_url = f"https://apix.cisco.com/security/advisories/v2/cve/{cve_id}"

    api_response = requests.get(
        api_url,
        headers={"Authorization": f"Bearer {token}"}
    )

    if api_response.status_code == 404:
        return f"CVE {cve_id} was not found on CISCO advisories"

    if api_response.status_code != 200:
        return f"Eror connecting to the API: {api_response.status_code}"
    
    json_response = api_response.json()
    advisories = json_response.get("advisories", [])

    if not advisories:
        return f"No CISCO advisories for {cve_id}"
    
    advisory = advisories[0]
    
    summary_html = advisory.get("summary", "N/A")
    summary = BeautifulSoup(summary_html, "html.parser").get_text()

    formatted_response = f"""
    CVE: 
    {cve_id}
    Advisory: 
    {advisory.get('advisoryTitle', 'N/A')}
    Severity: 
    {advisory.get('sir', 'N/A')}
    CVSS Score: 
    {advisory.get('cvssBaseScore', 'N/A')}
    Summary: 
    {summary}
    Published: 
    {advisory.get('firstPublished', 'N/A')}
    URL: 
    {advisory.get('publicationUrl', 'N/A')}
    """
    return formatted_response

tools = [search_cisco_docs, search_web, search_cisco_vuln]

if __name__ == "__main__":
    print(search_cisco_docs.invoke("BGP neighbor down"))
    
    print(search_web.invoke("Cisco BGP troubleshooting 2026"))
        
    print(search_cisco_vuln.invoke("CVE-2023-20198"))