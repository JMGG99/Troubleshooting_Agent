# Cisco Troubleshooting Agent

An AI assistant that helps diagnose Cisco networking issues, retrieve relevant documentation, and check official advisories through a FastAPI backend powered by LangGraph and Claude.

## Architecture

```text
User → FastAPI → Agent (LangGraph + Claude)
                 ├── BGP Subagent (With cisco docs)
                 ├── Upgrade Subagent  (Specialized on C8200 and C8300 devices)
                 ├── RAG (Cisco PDFs)
                 ├── Web Search
                 └── Cisco PSIRT API (Designed to check info regarding CVE only, other info regarding versions could use Web search tool instead)
```

## Stack

Python, LangGraph, Claude, FAISS, FastAPI, SQLite.

## Setup locally

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies with `pip install -r requirements.txt`.
4. Create a `.env` file.
5. Run the API with `uvicorn main:app --reload`.

## Environment variables

Create a `.env` file with the following values:

```env
ANTHROPIC_API_KEY=your_anthropic_key
CISCO_CLIENT_ID=your_cisco_client_id
CISCO_CLIENT_SECRET=your_cisco_client_secret
HF_TOKEN=your_huggingface_token
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_TRACING=true
```

## Endpoints

### `GET /health`

Checks whether the API is running.

Example:

```bash
curl http://127.0.0.1:8000/health
```

### `POST /diagnose`

Sends a networking problem to the agent.

Example:

```bash
curl -X POST http://127.0.0.1:8000/diagnose \
  -H "Content-Type: application/json" \
  -d '{
    "problem": "BGP neighbor is down",
    "session_id": null
  }'
```

## Design decisions

### Why subagents?

Because different problems need different reasoning paths. A BGP issue, an upgrade question, and a vulnerability lookup are not the same task, so splitting them into subagents keeps the system clearer and easier to debug.

### Why RAG?

Because Cisco PDFs contain useful domain knowledge that the model should not have to guess from memory. RAG lets the agent retrieve relevant context before answering.

### Why SqliteSaver?

Because this is a V1 prototype and SQLite keeps session memory simple, local, and persistent without adding the complexity of a full database server.

## Notes

This project is intended as a practical portfolio prototype. Before using Cisco-related content or API integrations in production, it is recommended to review Cisco’s applicable legal terms, licenses, and usage policies.
