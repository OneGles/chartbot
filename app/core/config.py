import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    LLM_API_KEY = os.getenv("LLM_API_KEY")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL")
    LLM_MODEL = os.getenv("LLM_MODEL")
    EMBED_MODEL = os.getenv("EMBED_MODEL")

settings = Settings()
