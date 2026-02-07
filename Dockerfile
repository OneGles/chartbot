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
COPY app ./app
COPY scripts ./scripts
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


#docker compose build {discord-bot / upload-audio}
#docker compose up discord-bot / upload-audio
#@tasks.loop(time=time(hour=21, minute=31, second=0, tzinfo=TZ))
#https://platform.openai.com/chat
