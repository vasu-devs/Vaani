import logging
import asyncio
import os
import json
from datetime import datetime
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
    finally:
        await save_transcript(agent)

async def save_transcript(agent: VoicePipelineAgent):
    os.makedirs("call_logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"call_logs/log_{timestamp}.json"
    
    # Extract metadata (simple mock for specific fields if needed, or just dump messages)
    transcript = []
    risk_score = 0 # Mock logic or analyze text
    
    for msg in agent.chat_ctx.messages:
        # Avoid serializing non-serializable objects if any
        # ChatMessage usually has role (enum) and content (str/list)
        role_str = str(msg.role)
        content = msg.content
        if isinstance(content, list):
            content = " ".join([str(c) for c in content])
        
        transcript.append({
            "role": role_str,
            "content": content,
            "timestamp": datetime.now().isoformat() # Ideally capture real time if available
        })
        
        # Simple keyword risk analysis
        if "escalate" in str(content).lower() or "refuse" in str(content).lower():
            risk_score += 20
        if "sue" in str(content).lower() or "lawyer" in str(content).lower():
            risk_score += 50
            
    # Normalize risk
    risk_score = min(score for score in [risk_score] if True) # clean way to keep variable
    risk_score = min(100, risk_score)

    data = {
        "id": f"call-{timestamp}",
        "timestamp": timestamp,
        "transcript": transcript,
        "risk_score": risk_score,
        "status": "completed"
    }
    
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved transcript to {filename}")

if __name__ == "__main__":
    agents.cli.run_app(server)
