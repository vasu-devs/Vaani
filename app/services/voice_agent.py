import asyncio
import logging
import json
from dotenv import load_dotenv

from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
    tts,
    AgentSession,
)
from livekit.agents.voice import Agent as VoicePipelineAgent
from livekit.plugins import groq, deepgram, silero
from livekit import rtc

from app.core.config import Config
from app.services.transcript_manager import TranscriptManager

load_dotenv()
logger = logging.getLogger("debt-collector.agent")
_vad_instance = None

def get_vad():
    global _vad_instance
    if _vad_instance is None:
        _vad_instance = silero.VAD.load()
    return _vad_instance

class DebtCollectorAgent:
    def __init__(self, ctx: JobContext):
        self.ctx = ctx
        self.metadata = self.parse_metadata(ctx.job.metadata)
        self.transcript_manager = TranscriptManager()
        
        # Initialize components early for pre-warming
        requested_voice = self.metadata.get("agent_voice", Config.DEFAULT_AGENT_VOICE).lower()
        if requested_voice not in ["asteria", "luna", "stella", "zeus", "orion", "arcas"]:
             requested_voice = "arcas"

        SYS_PROMPT = f"""
        You are {self.metadata.get("agent_name", Config.DEFAULT_AGENT_NAME)}, a collections agent for RiverLine Bank.
        Your goal is to collect a debt of ${self.metadata.get("debt_amount", "100")} from {self.metadata.get("debtor_name", "John")}.
        
        **Tone:** Professional, Firm, but Polite.
        
        **Debtor Context:**
        {self.metadata.get("user_details", "")}
        
        **Instructions:**
        1. Verify you are speaking to {self.metadata.get("debtor_name", "John")}.
        2. State the debt amount clearly: ${self.metadata.get("debt_amount", "100")}.
        3. Listen to their reason for non-payment.
        4. Negotiation:
           - If they can pay now -> Ask for payment method (Card/ACH).
           - If they can't pay full -> Offer a plan (e.g. 50% now).
           - If they can't pay anything -> Ask for a promise to pay date.
           - If they refuse -> Mention potential credit score impact (politely).
           
        **Constraint:**
        - Keep responses short (1-2 sentences).
        - Use "Hmm", "I see" to acknowledge listening.
        - Do not be rude.
        """

        # Initialize Agent Components
        initial_ctx = llm.ChatContext()
        initial_ctx.add_message(role="system", content=SYS_PROMPT)

        self.agent = VoicePipelineAgent(
            vad=get_vad(),
            stt=deepgram.STT(model="nova-2-general", smart_format=False, sample_rate=8000), 
            llm=groq.LLM(model="llama-3.1-8b-instant"),
            tts=deepgram.TTS(model=f"aura-{requested_voice}-en", sample_rate=8000),
            min_endpointing_delay=1.0,
            max_endpointing_delay=10.0,
            instructions=SYS_PROMPT
        )

    def parse_metadata(self, metadata_str: str) -> dict:
        try:
            return json.loads(metadata_str)
        except:
             # Fallback to env vars if not provided in job
             return {
                "debtor_name": "John Doe", 
                "debt_amount": "N/A",  # Or handle better
                "agent_name": Config.DEFAULT_AGENT_NAME,
                "agent_voice": Config.DEFAULT_AGENT_VOICE,
                "user_details": ""
             }

    async def start(self):
        logger.info(f"Starting Agent for Room...")

        # Pre-connect to TTS immediately to overlap with room connection
        if self.agent:
             self.agent.tts.prewarm()

        # 1. Connect to Room (Force Relay if needed)
        # 1. Connect to Room (Auto-Negotiation + Audio Only Timeout)
        try:
            self.setup_events()
            logger.info("Connecting to room (Auto-Negotiating transport + Audio Only)...")
            await asyncio.wait_for(
                self.ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY), 
                timeout=30.0
            )
            logger.info("Connected to room successfully.")
        except asyncio.TimeoutError:
             logger.error("Connection timed out (10s). Network too slow or blocking UDP.")
             raise Exception("Connection Timeout")
        except Exception as e:
             logger.error(f"Connection failed: {e}")
             # If Auto fails, there is severe network trouble. Using default behavior.
             
        # 2. Refresh Metadata from Room (This is the Source of Truth from SIPHandler)
        if self.ctx.room.metadata:
            try:
                room_meta = json.loads(self.ctx.room.metadata)
                self.metadata.update(room_meta)
                logger.info(f"Updated Metadata from Room: {self.metadata}")
            except:
                logger.warning("Failed to parse room metadata")
                
        logger.info(f"Final Metadata: {self.metadata}")

        # Note: self.agent is already initialized in __init__
        debtor_name = self.metadata.get("debtor_name", "John")
        agent_name = self.metadata.get("agent_name", Config.DEFAULT_AGENT_NAME)

        # Initialize Agent Session and Start
        self.session = AgentSession()
        
        logger.info("Starting Agent Session...")
        await self.session.start(self.agent, room=self.ctx.room)
        
        # Initial Greeting
        await asyncio.sleep(0.5) # reduced wait
        
        logger.info(f"Attempting to say greeting to {debtor_name}...")
        try:
            # Sync call, keep handle alive
            self._greeting_handle = self.session.say(f"Hi {debtor_name}, this is {agent_name} from RiverLine.", allow_interruptions=False)
            logger.info(f"Greeting started (Handle: {self._greeting_handle})")
        except Exception as e:
            logger.error(f"Failed to say greeting: {e}")

    def setup_events(self):
        # Hook into room disconnect events for reliable saving
        @self.ctx.room.on("participant_disconnected")
        def on_participant_disconnected(participant: rtc.RemoteParticipant):
            logger.info(f"Participant disconnected: {participant.identity}")
            asyncio.create_task(self.protected_save())

        @self.ctx.room.on("disconnected")
        def on_room_disconnected(reason):
             logger.info(f"Room disconnected: {reason}")
             asyncio.create_task(self.protected_save())

    async def protected_save(self):
        """Wrapper for save_transcript with timeout"""
        try:
             # wait_for is important
             await asyncio.wait_for(
                self.transcript_manager.save_transcript(self.agent, self.agent.chat_ctx, self.metadata), 
                timeout=15.0
            )
        except Exception as e:
            logger.error(f"Save failed or timed out: {e}")

async def entrypoint(ctx: JobContext):
    """
    Entrypoint for the worker.
    """
    agent_instance = DebtCollectorAgent(ctx)
    try:
        await agent_instance.start()
    except Exception as e:
        logger.error(f"Agent runtime error: {e}")
        
    # Wait for completion (or disconnect)
    # The agent.start() above runs in background, but we need to keep the process alive
    # usually until the room is closed.
    try:
        # Wait indefinitely - the disconnect event will handle cleanup/saving
        # and eventually the job runner kills the task when room closes
        await asyncio.Event().wait() 
    except asyncio.CancelledError:
        logger.info("Job cancelled")
    finally:
        # Last ditch save
        await agent_instance.protected_save()
