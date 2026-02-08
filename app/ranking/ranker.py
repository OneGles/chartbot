from __future__ import annotations

import json
import math
from typing import Any, Dict, List, Tuple

from app.db.database import get_conn
from app.feedback.store import get_user_feedback_item_ids
from app.profile.models import UserProfile
from app.retrieval.search import search as vector_search

DOMAINS = ["film", "book", "music", "game"]


def _softmax(scores: List[float], temperature: float = 1.0) -> List[float]:
    if not scores:
        return []
    t = max(1e-6, float(temperature))
    m = max(scores)
    exps = [math.exp((s - m) / t) for s in scores]
    z = sum(exps) or 1.0
    return [e / z for e in exps]


def _norm(s: str) -> str:
    return " ".join(str(s).strip().split()).lower()


def _build_query(profile: UserProfile, domain: str) -> str:
    tags: List[str] = []
    tags += profile.likes_by_domain.get(domain, [])
    tags += profile.likes
    tags += profile.mood

    seeds = profile.seeds[:2]
    constraints = profile.constraints

    parts: List[str] = []
    if tags:
        parts.append(" ".join(tags))
    if seeds:
        parts.append("like " + " ".join(seeds))
    if constraints:
        parts.append(" ".join(constraints))

    return " ".join(parts).strip()


def _apply_constraints(results: List[Dict[str, Any]], profile: UserProfile, domain: str) -> List[Dict[str, Any]]:
    constraints = " ".join(profile.constraints + profile.dislikes + profile.dislikes_by_domain.get(domain, []))
    c = _norm(constraints)

    banned: List[str] = []
    if "no gore" in c or "gore" in c:
        banned.append("gore")
    # dopo Step 7, la forma canonica è "no jumpscare ..." quindi basta questo check
    if "jumpscare" in c:
        banned.append("jumpscare")

    out: List[Dict[str, Any]] = []
    for r in results:
        text = _norm(r.get("text", ""))
        tags = " ".join([_norm(x) for x in (r.get("tags") or [])])

        penalty = 0.0
        for b in banned:
            if b in text or b in tags:
                penalty += 0.10

        r2 = dict(r)
        r2["score"] = float(r2.get("score", 0.0)) - penalty
        out.append(r2)

    out.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    return out


def _filter_seeds(candidates: List[Dict[str, Any]], profile: UserProfile) -> List[Dict[str, Any]]:
    seed_set = {_norm(s) for s in profile.seeds}
    out: List[Dict[str, Any]] = []
    for c in candidates:
        title = _norm(c.get("title", ""))
        if title and title in seed_set:
            continue
        out.append(c)
    return out


def _fetch_items_meta(item_ids: List[int]) -> List[Dict[str, Any]]:
    if not item_ids:
        return []
    qmarks = ",".join(["?"] * len(item_ids))
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            f"SELECT metadata_json FROM items WHERE id IN ({qmarks})",
            item_ids,
        )
        rows = cur.fetchall()

    out: List[Dict[str, Any]] = []
    for (mj,) in rows:
        try:
            out.append(json.loads(mj) if mj else {})
        except Exception:
            out.append({})
    return out


def _extract_pref(meta_list: List[Dict[str, Any]]) -> Tuple[set[str], set[str]]:
    tags: set[str] = set()
    people: set[str] = set()
    for m in meta_list:
        for t in (m.get("tags") or []):
            tags.add(_norm(t))
        for p in (m.get("people") or []):
            people.add(_norm(p))
    return tags, people


def _apply_feedback_bias(
    candidates: List[Dict[str, Any]],
    liked_tags: set[str],
    liked_people: set[str],
    disliked_tags: set[str],
    disliked_people: set[str],
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    for c in candidates:
        score = float(c.get("score", 0.0))
        tags = {_norm(t) for t in (c.get("tags") or [])}
        people = {_norm(p) for p in (c.get("people") or [])}

        # boost
        score += 0.05 * len(tags & liked_tags)
        score += 0.08 * len(people & liked_people)

        # penalty
        score -= 0.05 * len(tags & disliked_tags)
        score -= 0.08 * len(people & disliked_people)

        c2 = dict(c)
        c2["score"] = score
        out.append(c2)

    out.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    return out


def recommend_bundle(profile: UserProfile, user_id: int, top_k_per_domain: int = 8) -> Dict[str, Any]:
    liked_ids, disliked_ids = get_user_feedback_item_ids(user_id)

    liked_meta = _fetch_items_meta(liked_ids)
    disliked_meta = _fetch_items_meta(disliked_ids)

    liked_tags, liked_people = _extract_pref(liked_meta)
    disliked_tags, disliked_people = _extract_pref(disliked_meta)

    per_domain: Dict[str, List[Dict[str, Any]]] = {}
    for domain in DOMAINS:
        q = _build_query(profile, domain) or "popular"

        candidates = vector_search(domain, q, top_k=top_k_per_domain)
        candidates = _filter_seeds(candidates, profile)
        candidates = _apply_constraints(candidates, profile, domain)
        candidates = _apply_feedback_bias(candidates, liked_tags, liked_people, disliked_tags, disliked_people)

        if not candidates:
            candidates = vector_search(domain, "popular " + domain, top_k=top_k_per_domain)
            candidates = _filter_seeds(candidates, profile)
            candidates = _apply_constraints(candidates, profile, domain)
            candidates = _apply_feedback_bias(candidates, liked_tags, liked_people, disliked_tags, disliked_people)

        per_domain[domain] = candidates

    bundle: Dict[str, Any] = {}
    for domain, candidates in per_domain.items():
        if not candidates:
            bundle[domain] = None
            continue

        scores = [float(c.get("score", 0.0)) for c in candidates]
        probs = _softmax(scores, temperature=0.8)

        best = dict(candidates[0])
        best["p"] = probs[0]
        best["reason_tags"] = _collect_reason_tags(profile, best, domain)

        bundle[domain] = best

    return {
        "queries": {d: _build_query(profile, d) for d in DOMAINS},
        "bundle": bundle,
        "feedback": {
            "liked_item_ids": liked_ids,
            "disliked_item_ids": disliked_ids,
        },
    }


def _collect_reason_tags(profile: UserProfile, item: Dict[str, Any], domain: str) -> List[str]:
    wants = [_norm(x) for x in (profile.likes_by_domain.get(domain, []) + profile.mood)]
    tags = [_norm(x) for x in (item.get("tags") or [])]

    overlap: List[str] = []
    for w in wants:
        for t in tags:
            if w and (w in t or t in w):
                overlap.append(w)

    out: List[str] = []
    seen = set()
    for x in overlap:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return out[:5]
