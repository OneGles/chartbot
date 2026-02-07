FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

#Gestione sqlite
RUN apt-get update \
 && apt-get install -y --no-install-recommends sqlite3 \
 && rm -rf /var/lib/apt/lists/*

# Dipendenze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Codice
COPY . .
COPY scripts ./scripts
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


#docker compose build 
#docker compose up 
#https://platform.openai.com/chat
#docker compose exec api python -m scripts.load_items
#docker compose exec api python -m scripts.build_index

#{
#  "user_id": 1,
#  "message": "Mi piacciono i thriller psicologici, niente gore. Film tipo Shutter Island."
#}

#{
#  "user_id": 1,
#  "message": "Nei videogiochi voglio horror narrativi e psicologici, niente jumpscare continui."
#}

#{
#  "user_id": 1,
#  "message": "Musica: dark ambient e colonne sonore tese, atmosfera cupa."
#}



