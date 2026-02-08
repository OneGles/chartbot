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


A) Normalizzazione profilo (qualità)

dedup intelligente, mapping IT/EN per tag comuni

canonicalizzazione constraints

B) Feedback loop (events)

endpoint /feedback (like/dislike su item)

salva su tabella events

usa feedback per bias nel ranking (boost/penalty per tag/people)

C) API di raccomandazione “pulita”

endpoint /recommend che non aggiorna profilo, ma genera solo consigli

/chat resta per aggiornare profilo

D) “Session memory” corretta

summary solo gusto (già quasi ok)

niente contaminazioni

E) Demo/portfolio

README con architettura + screenshot

script make demo (o powershell) per: init db, load items, build index, run

(opzionale) UI minimale (React/Next o anche solo una pagina HTML)

Se fai A+B+C+D sei già “portfolio ready”. La UI è extra.