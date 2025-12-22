import os
from dotenv import load_dotenv

# Load .env file
load_dotenv(dotenv_path=".env.local")
load_dotenv()

class Config:
    # LiveKit
    LIVEKIT_URL = os.getenv("LIVEKIT_URL")
    LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
    LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
    
    # SIP / Telephony
    SIP_OUTBOUND_TRUNK_ID = os.getenv("SIP_OUTBOUND_TRUNK_ID")
    
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

# Validate on import (optional, can be explicit)
# Config.validate()
