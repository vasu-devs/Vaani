import logging
import asyncio
import os
from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import Agent, AgentServer, AgentSession, room_io, llm
from livekit.agents.voice import Agent as VoicePipelineAgent
from livekit.plugins import noise_cancellation, deepgram, groq, silero

# Load env vars
load_dotenv(dotenv_path=".env.local")
load_dotenv()

logger = logging.getLogger("debt-collector")

class DebtCollectionAgent(Agent):
    # Class wrapping not strictly needed for PipelineAgent but good for keeping structure
    pass

server = AgentServer()


@server.rtc_session()
async def my_agent(ctx: agents.JobContext):
    logger.info("Starting Groq + Deepgram Agent")
    
    # Initialize VAD
    vad = silero.VAD.load()

    # Create the Agent configuration
    agent = VoicePipelineAgent(
        vad=vad,
        stt=deepgram.STT(),
        llm=groq.LLM(
            model="llama-3.1-8b-instant",
        ),
        tts=deepgram.TTS(),
        instructions="""
You are Rachel, a professional and empathetic debt collection agent for Riverline Bank.
Your goal is to collect a debt of $1,500 for a credit card ending in 4321.

Instructions:
1. Verify Identity: Always start by asking if you are speaking to the account holder.
2. State Purpose: Once verified, calmly state that you are calling regarding an overdue balance of $1,500.
3. Negotiate: If the user cannot pay the full amount, ask what they can afford today. Minimum payment for good standing is $500.
4. Closing: Once a payment amount/plan is agreed, thank them and end the call. If refused, politely inform of escalation and end.
5. Tone: Polite, firm, human-like.
Do not use markdown. Speak clearly.
"""
    )
    
    session = AgentSession()

    await session.start(room=ctx.room, agent=agent)
    
    # Send initial greeting
    await session.generate_reply(
        instructions="Greet the user, introduce yourself as Rachel from Riverline Bank, and ask if you are speaking with the account holder."
    )
    
    # Monitor for disconnect
    try:
        await ctx.room.disconnect_future
    except:
        pass

if __name__ == "__main__":
    agents.cli.run_app(server)
