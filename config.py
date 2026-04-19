"""
config.py — April's configuration
All settings are loaded from the .env file.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# ─── Required Settings ────────────────────────────────────────────────────────
TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
OWNER_CHAT_ID: int = int(os.getenv("OWNER_CHAT_ID", "0"))

# ─── Optional / Cloud Settings ───────────────────────────────────────────────
WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "").rstrip("/")   # e.g. https://april-xxx.railway.app
PORT: int = int(os.getenv("PORT", "8080"))
DB_PATH: str = os.getenv("DB_PATH", "april_memory.db")

# ─── AI Model Settings ───────────────────────────────────────────────────────
MODEL: str = "llama-3.3-70b-versatile"  # Best free model on Groq
MAX_HISTORY: int = 30                   # Messages kept in context window
MAX_TOKENS: int = 1024                  # Max tokens per reply


def validate_config():
    """Fail fast if required environment variables are missing."""
    errors = []

    if not TELEGRAM_TOKEN:
        errors.append("TELEGRAM_TOKEN is missing — get it from @BotFather on Telegram")
    if not GROQ_API_KEY:
        errors.append("GROQ_API_KEY is missing — get it free at https://console.groq.com")
    if OWNER_CHAT_ID == 0:
        errors.append("OWNER_CHAT_ID is missing — get it from @userinfobot on Telegram")

    if errors:
        print("\n❌ April cannot start — fix these issues in your .env file:\n")
        for error in errors:
            print(f"   • {error}")
        print()
        sys.exit(1)
