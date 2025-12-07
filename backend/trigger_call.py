# trigger_call.py
import asyncio
import os
from dotenv import load_dotenv
from livekit import api

load_dotenv()

async def main():
    # 1. Initialize API Client
    lkapi = api.LiveKitAPI(
        os.getenv('LIVEKIT_URL'),
        os.getenv('LIVEKIT_API_KEY'),
        os.getenv('LIVEKIT_API_SECRET')
    )

    # 2. Configuration
    SIP_TRUNK_ID = "ST_..."  # <--- Get this from LiveKit Cloud Dashboard > SIP
    MY_PHONE_NUMBER = "+919876543210" # <--- YOUR VERIFIED NUMBER (E.164 format)
    
    print(f"Dialing {MY_PHONE_NUMBER}...")

    # 3. Create the SIP Participant (This triggers the call)
    try:
        await lkapi.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=SIP_TRUNK_ID,
                sip_call_to=MY_PHONE_NUMBER,
                room_name="call-room-001", # Agent will join this room
                participant_identity="user_phone",
                participant_name="Customer",
            )
        )
        print("Call initiated! Check your phone.")
    except Exception as e:
        print(f"Error dialing: {e}")
    finally:
        await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(main())