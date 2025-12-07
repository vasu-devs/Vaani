import logging
import os
from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import google

load_dotenv()

# Configuration
os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY_HERE" # Or load from .env

async def entrypoint(ctx: JobContext):
    # 1. Connect to the room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # 2. Configure Gemini 2.0 Flash (Multimodal Live)
    # We use the 'RealtimeModel' which handles audio I/O natively
    model = google.beta.realtime.RealtimeModel(
        model="gemini-2.0-flash-exp",
        instructions=(
            "You are Alex, a debt collector for RiverBank. "
            "Your goal is to collect a debt of $500. "
            "1. Verify the user's identity (ask for full name). "
            "2. Inform them of the overdue balance. "
            "3. Negotiate a payment date. "
            "Be polite but firm. Keep responses short and conversational."
        ),
        voice="Puck", # Options: Puck, Charon, Kore, Fenrir, Aoede
        temperature=0.6,
    )

    # 3. Create the Assistant
    agent = VoiceAssistant(
        vad=None,  # Gemini handles VAD (Voice Activity Detection) internally
        stt=None,  # Gemini handles Hearing internally
        llm=model, # Gemini handles Thinking internally
        tts=None,  # Gemini handles Speaking internally
        chat_ctx=llm.ChatContext(),
    )

    # 4. Start the Agent
    agent.start(ctx.room)

    # 5. Send initial greeting (The agent "thinks" of a greeting based on instructions)
    await agent.say("Hello? Is this the account holder?", allow_interruptions=True)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))