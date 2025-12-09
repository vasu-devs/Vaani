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
    
    # Validate Deepgram Voice Model (Apollo is not a valid Aura model, use Arcas as fallback)
    if "apollo" in agent_voice.lower():
        logger.warning(f"Voice '{agent_voice}' might be invalid/unavailable in Deepgram Aura. Falling back to 'arcas'.")
        agent_voice = "arcas"

    tts_model = f"aura-{agent_voice}-en"
    logger.info(f"Initializing TTS with model: {tts_model}")
    tts_plugin = deepgram.TTS(model=tts_model)
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

    logger.info("Connecting to room with forced TCP/Relay (Firewall Bypass)...")
    # Force TCP/TLS to bypass restrictive UDP firewalls
    try:
        rtc_config = rtc.RtcConfiguration(
            ice_transport_type=rtc.IceTransportType.TRANSPORT_RELAY
        )
        await ctx.connect(rtc_config=rtc_config)
        logger.info("Connected to room via TCP/Relay.")
    except Exception as e:
        logger.error(f"Failed to connect with forced TCP: {e}")
        # Fallback to default if this fails usually won't work if UDP is blocked but worth trying
        logger.info("Falling back to default connection...")
        await ctx.connect()

    logger.info("Starting AgentSession...")
    await session.start(room=ctx.room, agent=agent)
    # Monitor for disconnect
    egress_id = None
    lk_api = None
    
    # Flag to ensure we only save once
    is_saved = False

    async def protected_save():
        nonlocal is_saved
        if is_saved:
            return
        is_saved = True
        logger.info("Triggering protected transcript save...")
        try:
            full_config = {
                "debtor_name": debtor_name,
                "debt_amount": debt_amount,
                "agent_name": agent_name,
                "agent_voice": agent_voice,
                "user_details": user_details
            }
            # Execute save with timeout
            await asyncio.wait_for(save_transcript(agent, full_config), timeout=15.0)
            logger.info("Transcript save completed successfully.")
        except Exception as e:
            logger.error(f"Failed to save transcript: {e}")

    # Hook into Room events for faster detection of end-of-call
    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        logger.info(f"Participant disconnected: {participant.identity}")
        asyncio.create_task(protected_save())

    @ctx.room.on("disconnected")
    def on_room_disconnected(reason):
        logger.info(f"Room disconnected: {reason}")
        asyncio.create_task(protected_save())

    # --- BONUS: Egress Recording (Disabled for Stability) ---
    # Uncomment to enable if S3 is fully configured
    # try:
    #     lk_api = api.LiveKitAPI(
    #         os.getenv("LIVEKIT_URL"),
    #         os.getenv("LIVEKIT_API_KEY"),
    #         os.getenv("LIVEKIT_API_SECRET")
    #     )
    #     file_output = api.EncodedFileOutput(
    #         filepath=f"recordings/{ctx.room.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    #     )
    #     request = api.RoomCompositeEgressRequest(
    #         room_name=ctx.room.name,
    #         layout="grid",
    #         file=file_output
    #     )
    #     egress_info = await lk_api.egress.start_room_composite_egress(request)
    #     egress_id = egress_info.egress_id
    #     logger.info(f"Egress started: {egress_id}")
    # except Exception as e:
    #     logger.warning(f"Egress/Recording skipped: {e}")
    # --------------------------------------------------------

    logger.info("AgentSession started.")
    
    # Wait for connection to stabilize
    await asyncio.sleep(1)

    # Send initial greeting
    logger.info("Generating initial reply...")
    await session.generate_reply(
        instructions=f"Say specifically: 'Hi, this is {agent_name} from RiverLine Bank. Am I speaking with {debtor_name}?'"
    )
    logger.info("Initial reply generated.")
    
    try:
        logger.info("Waiting for call to end...")
        # Wait indefinitely until the task is cancelled (which happens on disconnect)
        await asyncio.get_running_loop().create_future()
    except asyncio.CancelledError:
        logger.info("Agent task cancelled.")
        # Ensure save is called if it hasn't been yet (e.g. agent shutdown manually)
        await protected_save()
    except Exception as e:
        logger.info(f"Agent session ending due to: {e}")
        await protected_save()
    finally:
        logger.info("Cleaning up session...")
        # Stop Egress if running
        if egress_id and lk_api:
             try:
                 pass
             except:
                 pass
        
        # Last ditch save attempt
        await protected_save()

async def analyze_risk(agent: VoicePipelineAgent, transcript_text: str, metadata: dict) -> dict:
    """
    Uses the Agent's LLM to analyze the transcript and predict risk.
    """
    try:
        logger.info("Starting Advanced Risk Analysis with Groq/Llama-3...")
        prompt = f"""
        Analyze the following debt collection call transcript.
        
        **Context:**
        Debtor: {metadata.get('debtor_name')}
        Debt Amount: {metadata.get('debt_amount')}
        User Details: {metadata.get('user_details')}

        **Transcript:**
        {transcript_text}

        **Task:**
        1. Determine the 'Risk Score' (0-100). 100 = High Risk (Refusal/Hostile), 0 = Low Risk (Paid/Plan Agreed).
        2. Provide a 'Reason' (Max 1 sentence).
        3. Extract 'Actionable Status' (e.g., "Paid", "Promise to Pay", "Refused", "Callback").

        **Output Format:**
        Return ONLY valid JSON:
        {{
            "risk_score": 85,
            "reason": "Customer shouted and refused to acknowledge debt.",
            "status": "Refused"
        }}
        """
        
        chat_ctx = llm.ChatContext()
        chat_ctx.add_message(role="user", content=prompt)
        stream = agent.llm.chat(chat_ctx=chat_ctx)
        
        response_text = ""
        async for chunk in stream:
            response_text += chunk.choices[0].delta.content or ""
            
        # Clean potential markdown code blocks
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse Risk Analysis JSON: {response_text}")
            return {"risk_score": 50, "reason": "Analysis Parse Error", "status": "Unknown"}
            
    except Exception as e:
        logger.error(f"Risk Analysis Failed: {e}")
        return {"risk_score": 50, "reason": "Analysis Failed", "status": "Unknown"}

async def save_transcript(agent: VoicePipelineAgent, metadata: dict):
    logger.info("Saving transcript... (Entry)")
    try:
        os.makedirs("call_logs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"call_logs/log_{timestamp}.json"
        
        transcript = []
        full_text = []
        
        # Access messages
        messages = []
        if hasattr(agent.chat_ctx, "messages"):
            messages = agent.chat_ctx.messages
        elif hasattr(agent.chat_ctx, "_items"):
            messages = agent.chat_ctx._items
        else:
            try:
                messages = list(agent.chat_ctx)
            except:
                logger.warning("Could not extract messages from ChatContext")
        
        for msg in messages:
            role = getattr(msg, "role", "unknown")
            content = getattr(msg, "content", "")
            if isinstance(content, list):
                content = " ".join([str(c) for c in content])
            
            # Map roles to human-readable names
            speaker = str(role)
            if role == "system":
                continue # Skip system prompt in saved transcript log
            elif role == "user":
                speaker = metadata.get("debtor_name", "Defaulter")
            elif role == "assistant":
                speaker = metadata.get("agent_name", "Agent")
                
            transcript.append({
                "role": str(role),
                "speaker": speaker,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
            full_text.append(f"{speaker}: {content}")
            
        # Perform Advanced Risk Analysis
        transcript_text = "\n".join(full_text)
        if transcript_text:
            analysis_result = await analyze_risk(agent, transcript_text, metadata)
        else:
            analysis_result = {"risk_score": 0, "reason": "No conversation recorded.", "status": "Error"}
            
        data = {
            "id": f"call-{timestamp}",
            "timestamp": timestamp,
            "metadata": metadata, 
            "transcript": transcript,
            "risk_analysis": analysis_result,
            "risk_score": analysis_result.get("risk_score", 0), # Backward compatibility
            "status": "completed"
        }
        
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved transcript and analysis to {filename}")
    except Exception as e:
        logger.error(f"Failed to save transcript: {e}")

if __name__ == "__main__":
    agents.cli.run_app(server)
