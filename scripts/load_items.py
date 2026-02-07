import json
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

from app.db.database import get_conn

ALLOWED_DOMAINS = {"film", "book", "music", "game"}


def _norm_list(xs: Any) -> list[str]:
    if not isinstance(xs, list):
        return []
    out: list[str] = []
    seen = set()
    for x in xs:
        s = str(x).strip()
        if not s:
            continue
        key = s.lower()
        if key in seen:
            continue
        out.append(s)
        seen.add(key)
    return out


def validate_item(obj: Dict[str, Any]) -> Dict[str, Any]:
    domain = obj.get("domain")
    title = obj.get("title")
    text = obj.get("text")

    if domain not in ALLOWED_DOMAINS:
        raise ValueError(f"invalid domain: {domain}")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("missing/invalid title")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("missing/invalid text")

    tags = _norm_list(obj.get("tags"))
    people = _norm_list(obj.get("people"))
    year = obj.get("year", None)
    if year is not None and not isinstance(year, int):
        year = None

    return {
        "domain": domain,
        "title": title.strip(),
        "text": text.strip(),
        "tags": tags,
        "people": people,
        "year": year,
    }


def iter_jsonl(path: Path) -> Iterable[Tuple[int, Dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            yield line_no, json.loads(line)


def main():
    path = Path("data/raw/items.jsonl")
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    inserted = 0
    skipped = 0

    with get_conn() as conn:
        cur = conn.cursor()

        for line_no, raw in iter_jsonl(path):
            try:
                item = validate_item(raw)
            except Exception as e:
                skipped += 1
                print(f"[SKIP] line {line_no}: {e}")
                continue

            domain = item["domain"]
            title = item["title"]

            metadata = {
                "text": item["text"],
                "tags": item["tags"],
                "people": item["people"],
            }
            if item["year"] is not None:
                metadata["year"] = item["year"]

            try:
                cur.execute(
                    "INSERT INTO items (domain, title, metadata_json) VALUES (?, ?, ?)",
                    (domain, title, json.dumps(metadata, ensure_ascii=False)),
                )
                inserted += 1
            except Exception:
                # most likely unique constraint hit
                skipped += 1

        conn.commit()

    print(f"Inserted: {inserted}, skipped: {skipped}")


if __name__ == "__main__":
    main()
