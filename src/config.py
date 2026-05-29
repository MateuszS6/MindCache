import os
from dotenv import load_dotenv

load_dotenv()

# --- openai ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- main config ---
MAX_INPUT_LENGTH = 1000
MAX_REQUESTS_PER_MINUTE = 5
RETRY_LIMIT = 2
AI_TIMEOUT_SECONDS = 10
MAX_OUTPUT_TOKENS = 200

# --- database ---
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "pass")
POSTGRES_DB = os.getenv("POSTGRES_DB", "summarydb")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "db")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)
