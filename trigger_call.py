import os
import asyncio
from livekit import api
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")
load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
SIP_TRUNK_ID = os.getenv("SIP_OUTBOUND_TRUNK_ID")

async def trigger_call(phone_number):
    if not SIP_TRUNK_ID:
        print("Error: SIP_OUTBOUND_TRUNK_ID not set in .env")
        return

    print(f"Triggering call to {phone_number}...")
    
    lk_api = api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    
    room_name = f"call-{phone_number.replace('+', '')}"
    
    # 1. Create Room (optional, joining creates it usually, but explicit is good)
    await lk_api.room.create_room(api.CreateRoomRequest(name=room_name))

    # 2. Dispatch SIP call
    # We use the SIPParticipant APIs if available, or just standard CreateSIPParticipant
    req = api.CreateSIPParticipantRequest(
        room_name=room_name,
        sip_trunk_id=SIP_TRUNK_ID,
        sip_call_to=phone_number,
        participant_identity=f"user-{phone_number}",
    )
    
    try:
        participant = await lk_api.sip.create_sip_participant(req)
        print(f"Call initiated! Participant ID: {participant.participant_id}")
        print(f"Room: {room_name}")
        print("Ensure 'agent.py' is running to pick up this room.")
    except Exception as e:
        print(f"Failed to trigger call: {e}")
    
    await lk_api.aclose()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python trigger_call.py <PHONE_NUMBER>")
        sys.exit(1)
    
    phone = sys.argv[1]
    asyncio.run(trigger_call(phone))
