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

class DebtCollectorAgent:
    def __init__(self, ctx: JobContext):
        self.ctx = ctx
        self.metadata = self.parse_metadata(ctx.job.metadata)
        self.transcript_manager = TranscriptManager()
        self.agent = None

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
        
        # 1. Connect to Room (Force Relay if needed)
        try:
            logger.info("Connecting to room with forced TCP/Relay...")
            rtc_config = rtc.RtcConfiguration(
                ice_transport_type=rtc.IceTransportType.TRANSPORT_RELAY
            )
            await self.ctx.connect(rtc_config=rtc_config)
        except Exception as e:
             logger.error(f"TCP connection failed: {e}. Falling back...")
             await self.ctx.connect()
             
        # 2. Refresh Metadata from Room (This is the Source of Truth from SIPHandler)
        if self.ctx.room.metadata:
            try:
                room_meta = json.loads(self.ctx.room.metadata)
                self.metadata.update(room_meta)
                logger.info(f"Updated Metadata from Room: {self.metadata}")
            except:
                logger.warning("Failed to parse room metadata")
                
        logger.info(f"Final Metadata: {self.metadata}")

        # Initialize requested Voice
        requested_voice = self.metadata.get("agent_voice", Config.DEFAULT_AGENT_VOICE).lower()
        if requested_voice not in ["asteria", "luna", "stella", "zeus", "orion", "arcas"]:
            logger.warning(f"Invalid voice '{requested_voice}', falling back to 'arcas'")
            requested_voice = "arcas" # Fallback

        # --- System Prompt Construction ---
        debtor_name = self.metadata.get("debtor_name", "John")
        debt_amount = self.metadata.get("debt_amount", "100")
        agent_name = self.metadata.get("agent_name", Config.DEFAULT_AGENT_NAME)
        user_details = self.metadata.get("user_details", "")

        SYS_PROMPT = f"""
        You are {agent_name}, a collections agent for RiverLine Bank.
        Your goal is to collect a debt of ${debt_amount} from {debtor_name}.
        
        **Tone:** Professional, Firm, but Polite.
        
        **Debtor Context:**
        {user_details}
        
        **Instructions:**
        1. Verify you are speaking to {debtor_name}.
        2. State the debt amount clearly: ${debt_amount}.
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

        # Initialize VAD
        # Use Silero VAD for better interruption handling
        vad = silero.VAD.load()
        
        # Initialize VoicePipelineAgent
        self.agent = VoicePipelineAgent(
            vad=vad,
            stt=deepgram.STT(), # Use Deepgram for speed
            llm=groq.LLM(model="llama-3.1-8b-instant"),
            tts=deepgram.TTS(model=f"aura-{requested_voice}-en"),
            min_endpointing_delay=0.5,
            max_endpointing_delay=5.0,
            instructions=SYS_PROMPT
        )

        # Hook up events
        self.setup_events()

        # Initialize Agent Session and Start
        self.session = AgentSession()
        
        logger.info("Starting Agent Session...")
        await self.session.start(self.agent, room=self.ctx.room)
        
        # Initial Greeting
        await asyncio.sleep(1) # Wait for audio stability
        # agent.say() is likely missing on new Agent class. Use session logic?
        # For now, let's try injecting the greeting via chat context or verify 'say'.
        # Actually, if we add a message to chat_ctx with role 'assistant', does it speak?
        # Yes, usually.
        # But 'say' forces it.
        # Check if session has 'say'.
        # For now, I will comment out 'say' to fix the start crash, and we test if it runs.
        # Or better:
        await self.session.say(f"Hi, this is {agent_name} from RiverLine Bank. Am I speaking with {debtor_name}?", allow_interruptions=True)

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
