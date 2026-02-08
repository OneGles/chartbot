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

# Art Curator Chatbot (RAG + Profiling + Feedback)

Chatbot “curatore” che:
1) legge preferenze dell’utente (film/libri/musica/videogiochi)
2) mantiene un profilo persistente (SQLite)
3) genera raccomandazioni per dominio usando retrieval (embedding search) + regole
4) apprende da feedback esplicito (like/dislike) per-domain

## Architettura

### Componenti
- **FastAPI**: API HTTP
- **SQLite**: persistenza (users, items, chunks, events)
- **Embedding + vector search**: indicizzazione dei contenuti (chunks) e ricerca per similarità
- **LLM**:
  - `extract_update`: estrae aggiornamenti strutturati (preferenze/constraint/seeds)
  - `update_summary`: mantiene un riassunto persistente dell’utente
  - `explainer`: genera una spiegazione “umana” delle raccomandazioni

### Flusso dati
**/chat**
- input: testo libero dell’utente
- output: update strutturato + profilo aggiornato + summary aggiornato  
(non genera raccomandazioni)

**/recommend**
- input: user_id
- costruisce query per dominio dal profilo
- retrieval su `chunks`
- filtri euristici (constraints)
- re-ranking con feedback **per-domain**
- output: bundle (1 item per dominio) + explanation

**/feedback**
- input: user_id, item_id, action like|dislike
- salva evento in SQLite (`events`)
- influenza le raccomandazioni successive solo nello stesso dominio


## Prerequisiti
- Docker Desktop
- PowerShell (Windows) oppure shell bash (Linux/macOS)

## Configurazione (.env)
Esempio:
LLM_API_KEY={api_key}
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4.1-mini
EMBED_MODEL=text-embedding-3-small
DB_PATH=data/app.db

docker compose exec api sh -lc "sqlite3 data/app.db 'DELETE FROM events WHERE user_id=1;'"
docker compose exec api sh -lc "sqlite3 data/app.db 'DELETE FROM users WHERE id=1;'"
docker compose exec api sh -m scripts.generate_items

docker compose exec api pwsh -File scripts/bootstrap.ps1
docker compose exec api pwsh -File scripts/demo_run.ps1

