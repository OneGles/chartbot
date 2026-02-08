docker compose build 
docker compose up 
https://platform.openai.com/chat
docker compose exec api python -m scripts.load_items
docker compose exec api python -m scripts.build_index

{
  "user_id": 1,
  "message": "Mi piacciono i thriller psicologici, niente gore. Film tipo Shutter Island."
}

{
  "user_id": 1,
  "message": "Nei videogiochi voglio horror narrativi e psicologici, niente jumpscare continui."
}

{
  "user_id": 1,
  "message": "Musica: dark ambient e colonne sonore tese, atmosfera cupa."
}


E) Demo/portfolio

README con architettura + screenshot

script make demo (o powershell) per: init db, load items, build index, run

(opzionale) UI minimale (React/Next o anche solo una pagina HTML)

Se fai A+B+C+D sei già “portfolio ready”. La UI è extra.

docker compose exec api sh -lc "sqlite3 data/app.db 'DELETE FROM events WHERE user_id=1;'"
docker compose exec api sh -lc "sqlite3 data/app.db 'DELETE FROM users WHERE id=1;'"
docker compose exec api sh -m scripts.generate_items

