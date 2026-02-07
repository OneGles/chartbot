from __future__ import annotations
import math
from typing import Any, Dict, List, Tuple

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
    return " ".join(s.strip().split()).lower()


def _build_query(profile: UserProfile, domain: str) -> str:
    # Preferenze dominio + mood + seeds (come "anchor" debole)
    tags = []
    tags += profile.likes_by_domain.get(domain, [])
    tags += profile.likes  # se in futuro lo usi
    tags += profile.mood

    # seeds: non tutti, al massimo 2, per non overfit
    seeds = profile.seeds[:2]

    # constraints: le trasformiamo in testo (MVP)
    constraints = profile.constraints

    parts = []
    if tags:
        parts.append(" ".join(tags))
    if seeds:
        parts.append("like " + " ".join(seeds))
    if constraints:
        parts.append(" ".join(constraints))

    return " ".join(parts).strip()


def _apply_constraints(results: List[Dict[str, Any]], profile: UserProfile, domain: str) -> List[Dict[str, Any]]:
    """
    MVP: penalizza item che contengono parole vietate nei tags/text.
    Non essendo un dataset perfetto, è euristico.
    """
    constraints = " ".join(profile.constraints + profile.dislikes + profile.dislikes_by_domain.get(domain, []))
    c = _norm(constraints)

    banned = []
    if "no gore" in c or "gore" in c:
        banned.append("gore")
    if "no continuous jumpscares" in c or "jumpscare" in c:
        banned.append("jumpscare")

    out = []
    for r in results:
        text = _norm(r.get("text", ""))
        tags = " ".join([_norm(x) for x in (r.get("tags") or [])])
        penalty = 0.0
        for b in banned:
            if b in text or b in tags:
                penalty += 0.10  # penalità fissa MVP
        r2 = dict(r)
        r2["score"] = float(r2.get("score", 0.0)) - penalty
        out.append(r2)

    out.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    return out

def _filter_seeds(candidates: List[Dict[str, Any]], profile: UserProfile) -> List[Dict[str, Any]]:
    seed_set = {_norm(s) for s in profile.seeds}
    out = []
    for c in candidates:
        title = _norm(c.get("title", ""))
        if title and title in seed_set:
            continue
        out.append(c)
    return out

def recommend_bundle(profile: UserProfile, top_k_per_domain: int = 8) -> Dict[str, Any]:
    per_domain: Dict[str, List[Dict[str, Any]]] = {}
    for domain in DOMAINS:
        q = _build_query(profile, domain) or "popular"
        candidates = vector_search(domain, q, top_k=top_k_per_domain)
        candidates = _filter_seeds(candidates, profile)
        candidates = _apply_constraints(candidates, profile, domain)

        if not candidates:
            # fallback: query più generica ma sempre filtrando seeds
            candidates = vector_search(domain, "popular " + domain, top_k=top_k_per_domain)
            candidates = _filter_seeds(candidates, profile)
            candidates = _apply_constraints(candidates, profile, domain)
            
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
    }


def _collect_reason_tags(profile: UserProfile, item: Dict[str, Any], domain: str) -> List[str]:
    # Motivi strutturati: overlap fra preferenze profilo e tags item
    wants = [_norm(x) for x in (profile.likes_by_domain.get(domain, []) + profile.mood)]
    tags = [_norm(x) for x in (item.get("tags") or [])]
    overlap = []
    for w in wants:
        for t in tags:
            if w and (w in t or t in w):
                overlap.append(w)
    # dedup e ritorno max 5
    out = []
    seen = set()
    for x in overlap:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return out[:5]
