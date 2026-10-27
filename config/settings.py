"""
MindCare AI — Application Settings
Loads all configuration from environment variables.
"""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# ─── Gemini (via OpenAI-compatible endpoint) ──────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY: str = GEMINI_API_KEY  # alias for compatibility
GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gemini-3-flash-preview")
FALLBACK_MODELS: list[str] = [
    m for m in dict.fromkeys([
        OPENAI_MODEL,
        "gemini-3-flash-preview",
        "gemini-flash-lite-latest",
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-3.6-flash",
        "gemini-3.8-flash"
    ]) if m
]
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1500"))
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "45"))


# ─── App ──────────────────────────────────────────────────────────────────────
APP_NAME: str = "MindCare AI"
APP_VERSION: str = "1.0.0"
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

# ─── Server ───────────────────────────────────────────────────────────────────
HOST: str = os.getenv("HOST", "127.0.0.1")
PORT: int = int(os.getenv("PORT", "8000"))

# ─── Database ─────────────────────────────────────────────────────────────────
DATABASE_PATH: str = os.getenv(
    "DATABASE_PATH",
    "/tmp/mindcare.db" if os.getenv("VERCEL") else "data/mindcare.db"
)

# ─── Safety ───────────────────────────────────────────────────────────────────
# Keywords that trigger crisis escalation
CRISIS_KEYWORDS: list[str] = [
    "suicide", "suicidal", "kill myself", "end my life",
    "want to die", "self-harm", "self harm", "hurt myself",
    "no reason to live", "better off dead"
]

CRISIS_HOTLINE: str = "iCall: 9152987821"
CRISIS_MESSAGE: str = (
    "I'm genuinely concerned about your safety right now. "
    "Please reach out to a crisis helpline immediately — "
    f"{CRISIS_HOTLINE}. You matter, and help is available 24/7."
)

# ─── Session ──────────────────────────────────────────────────────────────────
MAX_HISTORY_MESSAGES: int = int(os.getenv("MAX_HISTORY_MESSAGES", "6"))  # Max messages kept in memory per session
