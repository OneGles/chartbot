from fastapi import APIRouter
from pydantic import BaseModel

from app.profile.store import get_user_profile_and_summary, save_user_profile_and_summary
from app.profile.extractor import extract_update
from app.profile.summarizer import update_summary

router = APIRouter()


class ChatRequest(BaseModel):
    user_id: int
    message: str


@router.post("/chat")
def chat(req: ChatRequest):
    profile, summary = get_user_profile_and_summary(req.user_id)

    upd = extract_update(req.message, summary)
    profile.apply_update(upd)

    summary = update_summary(summary, req.message, profile)
    save_user_profile_and_summary(req.user_id, profile, summary)

    # Per ora: “assistant_message” minimale, poi lo sostituiremo con output RAG
    assistant_message = (
        "Ok. Ho aggiornato le tue preferenze. Quando vuoi posso consigliarti "
        "1 film, 1 libro, 1 musica e 1 videogioco coerenti con il tuo gusto."
    )

    return {
        "status": "ok",
        "assistant_message": assistant_message,
        "update": upd.model_dump(),
        "profile": profile.model_dump(),
        "summary": summary,
    }
