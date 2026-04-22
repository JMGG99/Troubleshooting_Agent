from fastapi import FastAPI
from agent import chat
from pydantic import BaseModel
import uuid

app = FastAPI()

class Request(BaseModel):
    problem: str
    session_id: str | None = None

class Response(BaseModel):
    AI_response: str
    session_id: str

@app.get("/health")
def health():
    return{"status":"OK"}

@app.post("/diagnose", response_model= Response)
def init_chat(data: Request):
    problem = data.problem
    session_id = data.session_id

    if session_id is None:
        session_id = str(uuid.uuid4())

    result = chat(problem, session_id)

    return Response(
        AI_response=result["diagnosis"],
        session_id=result["session_id"]
    )