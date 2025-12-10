import logging
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")
load_dotenv()

from livekit.agents import WorkerOptions, cli, AutoSubscribe, JobContext, JobProcess
from livekit.plugins import deepgram
from app.services.voice_agent import entrypoint
from app.core.config import Config

# Configure Logging
logging.basicConfig(level=logging.INFO)

async def request_fnc(ctx: JobContext):
    logging.info(f"Received job request: {ctx.job.id}")
    try:
        await ctx.accept()
        logging.info(f"Accepted job request: {ctx.job.id}")
    except Exception as e:
        logging.error(f"Failed to accept job request: {e}")
        raise

if __name__ == "__main__":
    # The CLI handles 'dev' and 'start' commands
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint, 
        request_fnc=request_fnc,
    ))
