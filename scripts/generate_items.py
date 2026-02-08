from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

OUT = Path("data/raw/items.jsonl")
SEED = 42

DOMAINS = ["film", "book", "music", "game"]

# Palette generi/toni differenti
GENRES = {
    "film": [
        ("thriller", ["thriller", "mystery", "twist"]),
        ("crime", ["crime", "detective", "noir"]),
        ("drama", ["drama", "character-driven", "emotional"]),
        ("comedy", ["comedy", "satire", "feel-good"]),
        ("romance", ["romance", "heartwarming", "relationships"]),
        ("sci-fi", ["sci-fi", "speculative", "mind-bending"]),
        ("fantasy", ["fantasy", "adventure", "epic"]),
        ("animation", ["animation", "family", "uplifting"]),
        ("horror", ["horror", "atmospheric", "psychological"]),
        ("action", ["action", "high-stakes", "fast-paced"]),
    ],
    "book": [
        ("thriller", ["thriller", "psychological", "twist"]),
        ("crime", ["crime", "mystery", "detective"]),
        ("literary", ["literary", "character-driven", "introspective"]),
        ("fantasy", ["fantasy", "epic", "worldbuilding"]),
        ("sci-fi", ["sci-fi", "speculative", "mind-bending"]),
        ("romance", ["romance", "heartwarming", "relationships"]),
        ("history", ["historical", "period", "drama"]),
        ("self-help", ["self-improvement", "habits", "practical"]),
        ("non-fiction", ["non-fiction", "insightful", "popular-science"]),
        ("horror", ["horror", "psychological", "dark"]),
    ],
    "music": [
        ("ambient", ["ambient", "atmospheric", "instrumental"]),
        ("classical", ["classical", "orchestral", "cinematic"]),
        ("jazz", ["jazz", "improvisation", "smooth"]),
        ("rock", ["rock", "energetic", "guitar"]),
        ("metal", ["metal", "aggressive", "heavy"]),
        ("pop", ["pop", "catchy", "uplifting"]),
        ("hip-hop", ["hip-hop", "groove", "beats"]),
        ("electronic", ["electronic", "club", "synth"]),
        ("folk", ["folk", "acoustic", "storytelling"]),
        ("soundtrack", ["soundtrack", "cinematic", "tense"]),
    ],
    "game": [
        ("rpg", ["rpg", "story-rich", "choices"]),
        ("action", ["action", "fast-paced", "combat"]),
        ("adventure", ["adventure", "exploration", "narrative"]),
        ("puzzle", ["puzzle", "mind-bending", "atmospheric"]),
        ("horror", ["horror", "psychological", "atmospheric"]),
        ("simulation", ["simulation", "relaxing", "creative"]),
        ("strategy", ["strategy", "tactical", "planning"]),
        ("sports", ["sports", "competitive", "skill-based"]),
        ("indie", ["indie", "creative", "unique"]),
        ("cozy", ["cozy", "chill", "feel-good"]),
    ],
}

# People "credibili" ma inventati (evitiamo IP reali): per portfolio va bene.
PEOPLE = {
    "film": {
        "director": ["A. Moretti", "L. Ferri", "S. Nakamura", "C. Dubois", "M. Alvarez", "R. Klein"],
        "writer": ["G. Rossi", "E. Bianchi", "T. Sato", "N. Martin", "P. Conti"],
    },
    "book": {
        "author": ["Elena Valli", "Marco Neri", "Sara Li", "Tomás Reyes", "Nina Keller", "Aya Tanaka"],
    },
    "music": {
        "artist": ["Northwave", "Blue Lantern", "Neon Atlas", "Quiet Lines", "Paper Planets", "Silver Kites"],
        "composer": ["I. Romano", "K. Yamato", "H. Weiss", "L. Contini"],
    },
    "game": {
        "studio": ["Studio Aurora", "IronFox", "Lumen Works", "Red Maple", "Nightjar", "Pixel Harbor"],
        "director": ["D. Marino", "K. Hoshino", "S. Berger", "A. Costa"],
    },
}

TEMPLATES = {
    "film": [
        "Un/Una {sub} {tone} in cui {hook}.",
        "Storia {tone} tra {hook}, con ritmo {pace}.",
        "Un film {sub} che punta su {hook} e un finale {twist}.",
    ],
    "book": [
        "Un romanzo {sub} {tone} su {hook}, con stile {style}.",
        "Libro {tone} che esplora {hook} e temi {theme}.",
        "Una storia {sub} con {hook} e un climax {pace}.",
    ],
    "music": [
        "Brani {tone} con sound {sound} e atmosfera {mood}.",
        "Un album {sub} {tone}: {sound}, {mood} e dinamiche {pace}.",
        "Musica {tone} pensata per {hook}, con taglio {sound}.",
    ],
    "game": [
        "Gioco {sub} {tone} dove {hook}; progressione {pace}.",
        "Esperienza {sub} con focus su {hook} e gameplay {pace}.",
        "Titolo {tone} che combina {hook} e una direzione artistica {mood}.",
    ],
}

TONE = ["leggero", "intenso", "coinvolgente", "rilassante", "adrenalinico", "riflessivo", "emotivo", "spensierato"]
PACE = ["lento", "moderato", "incalzante", "a episodi", "a crescita costante"]
TWIST = ["sorprendente", "ambiguo", "sottile", "forte", "inaspettato"]
STYLE = ["diretto", "poetico", "minimalista", "dettagliato", "ironico"]
THEME = ["umani", "sociali", "morali", "esistenziali", "familiari", "tecnologici"]
SOUND = ["sintetico", "organico", "orchestrale", "lo-fi", "analogico", "pulsante"]
MOOD = ["luminoso", "nostalgico", "sognante", "energico", "caldo", "freddo", "cinematico"]
HOOKS = {
    "film": [
        "un'indagine che ribalta la prospettiva",
        "un rapporto che si incrina lentamente",
        "una scelta morale impossibile",
        "un segreto di famiglia",
        "una corsa contro il tempo",
        "un triangolo di alleanze e tradimenti",
    ],
    "book": [
        "un mistero che cresce capitolo dopo capitolo",
        "un protagonista inaffidabile",
        "un viaggio di formazione",
        "un'idea scientifica che cambia tutto",
        "una relazione che sfida le convenzioni",
        "un ritorno al passato",
    ],
    "music": [
        "studio e concentrazione",
        "un viaggio notturno",
        "allenamento e carica",
        "relax serale",
        "lettura e focus",
        "una scena da film",
    ],
    "game": [
        "scelte che cambiano la storia",
        "esplorazione e scoperta",
        "sfide tattiche",
        "cooperazione e teamplay",
        "enigmi ambientali",
        "una narrazione simbolica",
    ],
}

def make_title(domain: str, genre: str, idx: int) -> str:
    # non IP reali
    prefixes = {
        "film": ["Echo", "Mirror", "City", "Signal", "Drift", "Lighthouse", "Paper", "Gravity"],
        "book": ["The", "A", "Beyond", "Under", "Between", "After", "Before", "Inside"],
        "music": ["Loops", "Frames", "Lines", "Textures", "Waves", "Signals", "Skylines", "Echoes"],
        "game": ["Project", "Chronicle", "Protocol", "Journey", "Vault", "Frontier", "Hollow", "Beacon"],
    }
    words = prefixes[domain]
    return f"{random.choice(words)} {genre.title()} {idx:03d}"

def make_people(domain: str) -> List[str]:
    if domain == "film":
        return [random.choice(PEOPLE["film"]["director"])]
    if domain == "book":
        return [random.choice(PEOPLE["book"]["author"])]
    if domain == "music":
        # mix artist + composer a volte
        if random.random() < 0.35:
            return [random.choice(PEOPLE["music"]["composer"])]
        return [random.choice(PEOPLE["music"]["artist"])]
    if domain == "game":
        if random.random() < 0.5:
            return [random.choice(PEOPLE["game"]["studio"])]
        return [random.choice(PEOPLE["game"]["director"])]
    return []

def make_text(domain: str, sub: str) -> str:
    tpl = random.choice(TEMPLATES[domain])
    return tpl.format(
        sub=sub,
        tone=random.choice(TONE),
        hook=random.choice(HOOKS[domain]),
        pace=random.choice(PACE),
        twist=random.choice(TWIST),
        style=random.choice(STYLE),
        theme=random.choice(THEME),
        sound=random.choice(SOUND),
        mood=random.choice(MOOD),
    )

def gen_items(per_domain: int = 100) -> List[Dict]:
    items: List[Dict] = []
    used_titles = set()

    for domain in DOMAINS:
        genre_defs = GENRES[domain]
        for i in range(per_domain):
            genre, base_tags = random.choice(genre_defs)
            title = make_title(domain, genre, i + 1)
            while title.lower() in used_titles:
                title = make_title(domain, genre, random.randint(1, 999))
            used_titles.add(title.lower())

            year = random.randint(1985, 2024)
            people = make_people(domain)

            # tags: base + 1-2 extra “mood”
            extra = []
            if random.random() < 0.6:
                extra.append(random.choice(["uplifting", "cozy", "dark", "tense", "romantic", "fun", "epic", "minimal"]))
            if random.random() < 0.35:
                extra.append(random.choice(["classic", "modern", "indie", "mainstream", "experimental"]))

            tags = list(dict.fromkeys(base_tags + extra))[:8]

            text = make_text(domain, genre)

            items.append(
                {
                    "domain": domain,
                    "title": title,
                    "year": year,
                    "people": people,
                    "tags": tags,
                    "text": text,
                }
            )

    return items

def main() -> None:
    random.seed(SEED)
    OUT.parent.mkdir(parents=True, exist_ok=True)

    items = gen_items(per_domain=100)  # -> 400 totali
    with OUT.open("w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    print(f"Wrote {len(items)} items to {OUT}")

if __name__ == "__main__":
    main()
