from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    user_id: int
    message: str

@router.post("/chat")
def chat(req: ChatRequest):
    return {
        "status": "ok",
        "echo": req.message
    }
