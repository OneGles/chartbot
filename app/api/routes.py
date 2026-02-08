from fastapi import APIRouter
from pydantic import BaseModel

from app.profile.store import get_user_profile_and_summary, save_user_profile_and_summary
from app.profile.extractor import extract_update
from app.profile.summarizer import update_summary
from app.retrieval.search import search as vector_search
from app.ranking.ranker import recommend_bundle
from app.ranking.explainer import explain
from app.feedback.store import add_event

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


class RecommendRequest(BaseModel):
    user_id: int
    top_k_per_domain: int = 8

@router.post("/recommend")
def recommend(req: RecommendRequest):
    profile, summary = get_user_profile_and_summary(req.user_id)

    rec = recommend_bundle(profile, req.user_id, top_k_per_domain=req.top_k_per_domain)
    explained = explain(summary, profile.constraints, rec["bundle"])

    return {
        "status": "ok",
        "profile": profile.model_dump(),
        "summary": summary,
        "recommendations": rec,
        "final": explained,
    }


class FeedbackRequest(BaseModel):
    user_id: int
    item_id: int
    action: str  # like|dislike

@router.post("/feedback")
def feedback(req: FeedbackRequest):
    add_event(req.user_id, req.item_id, req.action)
    return {"status": "ok"}


class SearchRequest(BaseModel):
    domain: str
    query: str
    top_k: int = 5

@router.post("/search")
def search_endpoint(req: SearchRequest):
    return {
        "domain": req.domain,
        "query": req.query,
        "results": vector_search(req.domain, req.query, req.top_k),
}
