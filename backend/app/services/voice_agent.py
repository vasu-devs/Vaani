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
    room_io,
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
        self.session = None

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

        self.sys_prompt = SYS_PROMPT

        # Initialize Agent Components
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
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse job metadata, using defaults: {e}")
            return {
                "debtor_name": "John Doe",
                "debt_amount": "N/A",
                "agent_name": Config.DEFAULT_AGENT_NAME,
                "agent_voice": Config.DEFAULT_AGENT_VOICE,
                "user_details": ""
            }

    async def start(self):
        logger.info("Starting Agent for Room...")

        # Pre-connect to TTS immediately to overlap with room connection
        # self.agent.tts.prewarm()  # removed: prewarm API changed in recent LiveKit Agents versions

        # 1. Connect to Room (Auto-Negotiation + Audio Only)
        try:
            logger.info("Connecting to room (Auto-Negotiating transport + Audio Only)...")
            await asyncio.wait_for(
                self.ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY),
                timeout=30.0
            )
            logger.info("Connected to room successfully.")
        except asyncio.TimeoutError:
            logger.error("Connection timed out (30s). Network too slow or blocking UDP.")
            raise Exception("Connection Timeout")
        except Exception as e:
            logger.error(f"Connection failed: {e}")

        # 2. Refresh Metadata from Room (Source of Truth from SIPHandler)
        if self.ctx.room.metadata:
            try:
                room_meta = json.loads(self.ctx.room.metadata)
                self.metadata.update(room_meta)
                logger.info(f"Updated Metadata from Room: {self.metadata}")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse room metadata: {e}")

        logger.info(f"Final Metadata: {self.metadata}")

        debtor_name = self.metadata.get("debtor_name", "John")
        agent_name = self.metadata.get("agent_name", Config.DEFAULT_AGENT_NAME)

        # 3. Wait for SIP participant to actually join (phone answered)
        logger.info("Waiting for SIP participant to join (phone to be answered)...")
        sip_participant = await self._wait_for_participant(timeout=60.0)

        if sip_participant is None:
            logger.warning("No SIP participant joined within timeout. Call may not have been answered.")
            return

        logger.info(f"SIP participant joined: {sip_participant.identity} (phone answered!)")

        # 4. Initialize Agent Session and Start — only after phone is answered
        self.session = AgentSession()

        # Setup disconnect events for transcript saving
        self.setup_events()

        logger.info("Starting Agent Session...")
        await self.session.start(
            self.agent,
            room=self.ctx.room,
        )

        # 5. Initial Greeting — phone is answered, safe to speak
        await asyncio.sleep(0.3)

        logger.info(f"Saying greeting to {debtor_name}...")
        try:
            self._greeting_handle = await self.session.say(
                f"Hi {debtor_name}, this is {agent_name} from RiverLine.",
                allow_interruptions=False
            )
            logger.info("Greeting sent successfully.")
        except Exception as e:
            logger.error(f"Failed to say greeting: {e}")

    async def _wait_for_participant(self, timeout: float = 60.0) -> rtc.RemoteParticipant:
        """Wait for a non-agent remote participant to join the room (i.e. the phone was answered)."""
        # Check if already present
        for p in self.ctx.room.remote_participants.values():
            if not p.identity.startswith("agent"):
                logger.info(f"SIP participant already in room: {p.identity}")
                return p

        # Wait for participant to connect
        participant_joined = asyncio.Event()
        joined_participant = None

        @self.ctx.room.on("participant_connected")
        def on_participant_connected(participant: rtc.RemoteParticipant):
            nonlocal joined_participant
            logger.info(f"Participant connected: {participant.identity}")
            if not participant.identity.startswith("agent"):
                joined_participant = participant
                participant_joined.set()

        try:
            await asyncio.wait_for(participant_joined.wait(), timeout=timeout)
            return joined_participant
        except asyncio.TimeoutError:
            logger.warning(f"Timed out waiting {timeout}s for SIP participant")
            return None

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
        if self.session is None:
            logger.warning("No session to save transcript from")
            return
        try:
            chat_ctx = getattr(self.session, 'history', None) or getattr(self.session, 'chat_ctx', None) or getattr(self.agent, 'chat_ctx', None)
            if chat_ctx is None:
                logger.warning("No chat context available for transcript save")
                return
            await asyncio.wait_for(
                self.transcript_manager.save_transcript(self.agent, chat_ctx, self.metadata),
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
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        logger.info("Job cancelled")
    finally:
        await agent_instance.protected_save()
