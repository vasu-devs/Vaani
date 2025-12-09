import logging
import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv

from livekit import agents, rtc, api
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
    
    # Load dynamic configuration
    # Priority: Room Metadata (per-call) > Env Vars (defaults) > Hardcoded
    
    # Fetch authoritative metadata from LiveKit Server
    config = {}
    try:
        lk_api = api.LiveKitAPI(
            os.getenv("LIVEKIT_URL"),
            os.getenv("LIVEKIT_API_KEY"),
            os.getenv("LIVEKIT_API_SECRET")
        )
        rooms = await lk_api.room.list_rooms(api.ListRoomsRequest(names=[ctx.room.name]))
        if rooms.rooms:
            server_room = rooms.rooms[0]
            if server_room.metadata:
                logger.info(f"Server metadata found: {server_room.metadata}")
                config = json.loads(server_room.metadata)
            else:
                logger.info("Server returned room, but no metadata.")
        else:
            logger.warning("Room not found via API.")
        await lk_api.aclose()
    except Exception as e:
        logger.warning(f"Failed to fetch server metadata: {e}")

    debtor_name = config.get("debtor_name") or os.environ.get("DEBTOR_NAME", "John Doe")
    debt_amount = config.get("debt_amount") or os.environ.get("DEBT_AMOUNT", "1500")
    agent_name = config.get("agent_name") or os.environ.get("AGENT_NAME", "Rachel")
    agent_voice = (config.get("agent_voice") or os.environ.get("AGENT_VOICE", "asteria")).lower()
    user_details = config.get("user_details") or os.environ.get("USER_DETAILS", "")

    logger.info(f"Configuration: Agent='{agent_name}', Voice='{agent_voice}', Debtor='{debtor_name}'")
    
    # Construct System Prompt
    system_prompt = f"""
CRITICAL OUTPUT RULES:

1. OUTPUT ONLY THE SPOKEN WORDS.

2. DO NOT use headers like "Turn 1:", "Plan B:", or "**Response:**".

3. DO NOT write post-call analysis or evaluations.

4. If you output a header, the system will CRASH.

You are '{agent_name}', a debt collection specialist for RiverLine Bank. You are speaking over the phone.

**CORE BEHAVIORS:**

1. **BREVITY IS KING:** You are a VOICE agent. You must keep responses short (under 40 words). Do not give speeches. Do not use bullet points. Do not read long lists of options.

2. **TONE:** Firm on the debt, soft on the person. Be empathetic but persistent.

3. **GOAL:** Verify the user's name, identify the reason for non-payment, and negotiate a payment plan for the ${debt_amount} overdue loan.

4. **NO NARRATION:** Do not output stage directions like "(waits for response)" or "(dialing)". Only output the words you speak.

**NEGOTIATION FLOW:**

1. Verify Identity ("Am I speaking with {debtor_name}?").

2. State Purpose (Loan is 30 days overdue, owe ${debt_amount}).

3. Discovery (Ask WHY they haven't paid).

4. Empathize & Pivot (Acknowledge their struggle, but pivot back to finding a solution).

5. Solution (Ask for full payment -> If no, offer partial payment -> If no, offer hardship plan).

**CRITICAL RULES:**

- If the user gets angry, acknowledge it briefly and move to a solution.

- Do not hallucinate legal threats.

- Do not make up address details; ask the user to confirm theirs.

- ONE question per turn. Do not stack questions.

- Do not summarize the total sum. State the monthly payment only.

**USER CONTEXT:**
The user's account details and notes: {user_details}

**Your First Line:** "Hi, this is {agent_name} from RiverLine Bank. Am I speaking with {debtor_name}?"
"""

    logger.info("Initializing components...")
    # Initialize VAD
    vad = silero.VAD.load()
    
    tts_model = f"aura-{agent_voice}-en"
    logger.info(f"Initializing TTS with model: {tts_model}")

    # Create the Agent configuration
    agent = VoicePipelineAgent(
        vad=vad,
        stt=deepgram.STT(),
        llm=groq.LLM(
            model="llama-3.1-8b-instant",
        ),
        tts=deepgram.TTS(model=tts_model),
        instructions=system_prompt
    )
    
    session = AgentSession()

    logger.info("Starting AgentSession...")
    await session.start(room=ctx.room, agent=agent)
    logger.info("AgentSession started.")
    
    # Wait for connection to stabilize
    await asyncio.sleep(1)

    # Send initial greeting
    logger.info("Generating initial reply...")
    await session.generate_reply(
        instructions=f"Say specifically: 'Hi, this is {agent_name} from RiverLine Bank. Am I speaking with {debtor_name}?'"
    )
    logger.info("Initial reply generated.")
    
    # Monitor for disconnect
    try:
        await ctx.room.disconnect_future
    except:
        pass
    finally:
        await save_transcript(agent)

async def save_transcript(agent: VoicePipelineAgent):
    try:
        os.makedirs("call_logs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"call_logs/log_{timestamp}.json"
        
        # Extract metadata (simple mock for specific fields if needed, or just dump messages)
        transcript = []
        risk_score = 0 # Mock logic or analyze text
        
        # Use internal _items to access messages directly, as ChatContext wrapper hides them
        messages = agent.chat_ctx._items if hasattr(agent.chat_ctx, "_items") else []

        for msg in messages:
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
    except Exception as e:
        logger.error(f"Failed to save transcript: {e}")

if __name__ == "__main__":
    agents.cli.run_app(server)
