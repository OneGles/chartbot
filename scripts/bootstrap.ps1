$ErrorActionPreference = "Stop"

Write-Host "== Bootstrap: ensure schema =="
sqlite3 data/app.db ".read app/db/schema.sql"

Write-Host "== Bootstrap: generate dataset (data/items.jsonl) =="
python -m scripts.generate_items

Write-Host "== Bootstrap: wipe demo tables (items/chunks/events/users) =="
# ordine: chunks -> items (FK), poi events, users
sqlite3 data/app.db @"
PRAGMA foreign_keys=OFF;
DELETE FROM chunks;
DELETE FROM items;
DELETE FROM events;
DELETE FROM users;
PRAGMA foreign_keys=ON;
"@

Write-Host "== Bootstrap: load items into DB =="
python -m scripts.load_items

Write-Host "== Bootstrap: build index (chunks + embeddings) =="
python -m scripts.build_index

Write-Host "== Bootstrap: create demo user (id=1) empty profile/summary =="
# profile_json e summary iniziali vuoti
sqlite3 data/app.db @"
INSERT INTO users (id, profile_json, summary)
VALUES (1, '{}', '');
"@

Write-Host "== Bootstrap: quick verify =="
sqlite3 data/app.db "SELECT domain, COUNT(*) FROM items GROUP BY domain;"
sqlite3 data/app.db "SELECT COUNT(*) AS chunks_count FROM chunks;"
sqlite3 data/app.db "SELECT COUNT(*) AS users_count FROM users;"
sqlite3 data/app.db "SELECT COUNT(*) AS events_count FROM events;"

Write-Host "== Bootstrap done =="
