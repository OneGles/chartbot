# ChArtbot 

Chatbot "artistico" che:
1) legge preferenze dell’utente in diversi campi artistici (film/libri/musica/videogiochi)
2) mantiene un profilo persistente e in aggiornamento (SQLite)
3) genera raccomandazioni per ogni dominio artistico
4) apprende da feedback esplicito (like/dislike) per-dominio

## Architettura

### Componenti
- **FastAPI**: API HTTP
- **SQLite**: persistenza dei dati (users, items, chunks, events)
- **Embedding + vector search**: indicizzazione dei contenuti (chunks) e ricerca per similarità
- **LLM**:
  - `extract_update`: estrae aggiornamenti strutturati (preferenze/constraint/seeds)
  - `update_summary`: mantiene un riassunto persistente delle preferenze dell’utente
  - `explainer`: genera una spiegazione comprensibile delle raccomandazioni

### Flusso dati (endpoint)
**/chat**
- input: testo libero dell’utente (l'utente esprime preferenze esplicite)
- output: update strutturato + profilo aggiornato + summary aggiornato

Formato input:
```bash
{
  "user_id": user_id,
  "message": "Message"
}
```

**/recommend**
- input: id dell'utente
- costruisce query per dominio dal profilo
- re-ranking con feedback aggiornati
- output: raccomandazioni (1 item per dominio) + spiegazione

Formato input:
```bash
{
  "user_id": user_id,
  "top_k_per_domain": numero_k
}
```

**/feedback**
- input: id utente, id item, action "like|dislike"
- salva evento in SQLite (`events`)
- influenza le raccomandazioni successive solo nello stesso dominio

Formato input:
```bash
{
  "user_id": user_id,
  "item_id": item_id,
  "action": "like/dislike"
}
```
## Prerequisiti
- Docker Desktop o Docker engine
- PowerShell (Windows) oppure shell bash (Linux/macOS)

## Configurazione (.env) (ROOT del progetto)
Per la creazione del file .env svolgere prima questi passaggi:
1. Crea un account su OpenAI (https://platform.openai.com)
2. Genera una API key (attivare Billing)
3. Crea il file .env in questo modo:
```env
LLM_API_KEY={api_key}
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4.1-mini
EMBED_MODEL=text-embedding-3-small
DB_PATH=data/app.db
```

## Docker container e demo
Scrivere su terminale:
```bash
docker compose build
docker compose up
```
- Andare su http://localhost:8000/docs e verificare che sia attivo

### Avvio demo (con Docker attivo)
Script di setup bootstrap.py:
```bash
docker compose exec api python -m scripts.bootstrap
```
Esegue automaticamente:
- inizializzazione DB
- generazione dataset (`data/raw/items.jsonl`)
- carica items su SQLite
- creazione chunks
- reset utente demo (id=1)

Script di avvio demo_run.py:
```bash
docker compose exec api python -m scripts.demo_run
```
Esegue automaticamente:
- reset utente con id=1 (per non avere la demo inquinata)
- creazione 3 preferenze dello user 1 a tema horror
- prima richiesta /recommend
- inserimento "like" alla canzone estratta in precedenza
- seconda richiesta /recommend
- Inserimento "dislike" al film precedente
- Terza richiesta /recommend

Se si vuole cambiare le preferenze iniziali in demo_run, modificarle direttamente dallo script e rifare la build e l'avvio di Docker.
In caso si volesse testare direttamente su fastAPI (anche per vedere TUTTI i dati nella struttura json) senza usare gli script di demo, andare su http://localhost:8000/docs e nella sezione di flusso dati di questo file per capire come scrivere la pipeline corretta per ogni endpoint.


## Eventuali errori
- **429 insufficient_quota**: Abilitare Billing su OpenAI.
- **sqlite3: not found**: installa `sqlite3` nel container oppure esegui i comandi DB dal tuo host.
- **ModuleNotFoundError: app**: esegui gli script come modulo (`python -m scripts.load_items`) e non come file.






