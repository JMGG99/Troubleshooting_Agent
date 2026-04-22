from fastapi.testclient import TestClient
from app.main import app
from app.rag import get_retriever
from app.tools import search_cisco_docs

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


def test_diagnose():
    response = client.post(
        "/diagnose",
        json={"problem": "BGP neighbor is down"}
    )

    assert response.status_code == 200

    data = response.json()
    assert "AI_response" in data
    assert "session_id" in data
    assert isinstance(data["AI_response"], str)
    assert isinstance(data["session_id"], str)

def test_retriever():
    retriever = get_retriever()
    results = retriever.invoke("BGP neighbor down")

    assert results is not None
    assert len(results) > 0


def test_tools():
    output = search_cisco_docs.invoke("BGP neighbor down")
    assert isinstance(output, str)
    assert len(output) > 0