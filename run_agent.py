import logging
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")
load_dotenv()

from livekit.agents import WorkerOptions, cli
from app.services.voice_agent import entrypoint

# Configure Logging
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    # The CLI handles 'dev' and 'start' commands
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
