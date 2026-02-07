from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

_CANON = {
    "psychological": "psicologico",
    "thriller": "thriller",
    "horror": "horror",
    "narrative": "narrativo",
    "dark": "cupo",
    "atmospheric": "atmosferico",
    "twist": "colpo di scena",
    "jumpscares": "jumpscare",
    "jumpscare": "jumpscare",
    "gore": "gore",
}


class UserUpdate(BaseModel):
    # Preferenze generiche (cross-domain)
    likes: List[str] = Field(default_factory=list)
    dislikes: List[str] = Field(default_factory=list)

    # Preferenze per dominio
    likes_by_domain: Dict[str, List[str]] = Field(default_factory=dict)
    dislikes_by_domain: Dict[str, List[str]] = Field(default_factory=dict)

    # “Semi” espliciti: titoli, autori, registi, artisti, giochi
    seeds: List[str] = Field(default_factory=list)

    # Vincoli espliciti: lingua, durata, piattaforme, ecc.
    constraints: List[str] = Field(default_factory=list)

    # Mood/atmosfera
    mood: List[str] = Field(default_factory=list)


class UserProfile(BaseModel):
    likes: List[str] = Field(default_factory=list)
    dislikes: List[str] = Field(default_factory=list)

    likes_by_domain: Dict[str, List[str]] = Field(default_factory=dict)
    dislikes_by_domain: Dict[str, List[str]] = Field(default_factory=dict)

    seeds: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    mood: List[str] = Field(default_factory=list)

    def apply_update(self, upd: UserUpdate) -> "UserProfile":
        def norm(s: str) -> str:
            s = " ".join(s.strip().split())
            if not s:
                return ""
            low = s.lower()
            return _CANON.get(low, s)

        def add_unique(dst: List[str], src: List[str]) -> List[str]:
            existing = {norm(x).lower() for x in dst}
            for x in src or []:
                x2 = norm(x)
                if not x2:
                    continue
                key = x2.lower()
                if key not in existing:
                    dst.append(x2)
                    existing.add(key)
            return dst

        def canon_no(x: str) -> str:
            x = norm(x)
            low = x.lower()
            if low.startswith("no "):
                rest = low[3:].strip()
                rest = _CANON.get(rest, rest)
                return f"no {rest}"
            return x

        # Merge lists
        self.likes = add_unique(self.likes, upd.likes)
        self.dislikes = add_unique(self.dislikes, upd.dislikes)
        self.seeds = add_unique(self.seeds, upd.seeds)
        self.constraints = add_unique(self.constraints, upd.constraints)
        self.mood = add_unique(self.mood, upd.mood)

        # Canonicalize constraints after merge (so we unify variants)
        self.constraints = [canon_no(x) for x in self.constraints]
        # Dedup again after canonicalization
        self.constraints = add_unique([], self.constraints)

        # Merge domain dicts
        for domain, vals in (upd.likes_by_domain or {}).items():
            self.likes_by_domain.setdefault(domain, [])
            self.likes_by_domain[domain] = add_unique(self.likes_by_domain[domain], vals)

        for domain, vals in (upd.dislikes_by_domain or {}).items():
            self.dislikes_by_domain.setdefault(domain, [])
            self.dislikes_by_domain[domain] = add_unique(self.dislikes_by_domain[domain], vals)

        # Defensive cleanup: seed titles must not appear in domain preference lists
        seed_set = {norm(x).lower() for x in self.seeds}
        for domain, vals in list(self.likes_by_domain.items()):
            self.likes_by_domain[domain] = [v for v in vals if norm(v).lower() not in seed_set]
        for domain, vals in list(self.dislikes_by_domain.items()):
            self.dislikes_by_domain[domain] = [v for v in vals if norm(v).lower() not in seed_set]

        return self

