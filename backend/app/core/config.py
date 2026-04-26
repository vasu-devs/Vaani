import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file — resolve relative to this file's location (backend/)
# config.py is at backend/app/core/config.py → need 3 levels up to reach backend/
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=_BACKEND_DIR / ".env.local")
load_dotenv()

class Config:
    # LiveKit
    LIVEKIT_URL = os.getenv("LIVEKIT_URL")
    LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
    LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
    
    # SIP / Telephony
    SIP_OUTBOUND_TRUNK_ID = os.getenv("SIP_OUTBOUND_TRUNK_ID")
    SIP_CALLER_ID = os.getenv("SIP_CALLER_ID")  # E.164 Twilio number, e.g. +12345678900
    
    # AI Models
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Defaults
    DEFAULT_AGENT_NAME = "Rachel"
    DEFAULT_AGENT_VOICE = "asteria" # Deepgram Aura voice
    
    @classmethod
    def validate(cls):
        required = ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "DEEPGRAM_API_KEY", "GROQ_API_KEY"]
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

# Validate on import is disabled — LiveKit CLI forks worker subprocesses
# where env vars may not be available. Call Config.validate() explicitly instead.
# Config.validate()
