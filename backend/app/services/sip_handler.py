import asyncio
import json
import logging
from livekit import api
from app.core.config import Config

logger = logging.getLogger("debt-collector.sip")

class SIPHandler:
    @staticmethod
    async def trigger_call(phone_number: str, metadata: dict = None):
        """
        Triggers an outbound SIP call using LiveKit.
        """
        if not Config.SIP_OUTBOUND_TRUNK_ID:
            raise ValueError("SIP_OUTBOUND_TRUNK_ID not set in configuration")

        if metadata is None:
            metadata = {}

        # Default metadata if not provided
        metadata.setdefault("debtor_name", "John Doe")
        metadata.setdefault("debt_amount", "1500")
        metadata.setdefault("agent_name", Config.DEFAULT_AGENT_NAME)
        metadata.setdefault("agent_voice", Config.DEFAULT_AGENT_VOICE)
        metadata.setdefault("user_details", "")

        logger.info(f"Triggering call to {phone_number}...")
        
        lk_api = api.LiveKitAPI(
            Config.LIVEKIT_URL, 
            Config.LIVEKIT_API_KEY, 
            Config.LIVEKIT_API_SECRET
        )
        
        room_name = f"call-{phone_number.replace('+', '')}"
        metadata_json = json.dumps(metadata)
        
        try:
            # 1. Ensure clean slate by deleting existing room
            try:
                await lk_api.room.delete_room(api.DeleteRoomRequest(room=room_name))
                logger.info(f"Deleted existing room: {room_name}")
            except Exception:
                pass # Room didn't exist, ignore

            # 2. Create Room with metadata (Atomic)
            await lk_api.room.create_room(
                api.CreateRoomRequest(name=room_name, metadata=metadata_json)
            )
            logger.info(f"Created fresh room {room_name} with metadata.")

            # 3. Dispatch SIP call
            req = api.CreateSIPParticipantRequest(
                room_name=room_name,
                sip_trunk_id=Config.SIP_OUTBOUND_TRUNK_ID,
                sip_call_to=phone_number,
                participant_identity=f"user-{phone_number}",
            )
            
            participant = await lk_api.sip.create_sip_participant(req)
            logger.info(f"Call initiated! Participant ID: {participant.participant_id}")
            return {
                "status": "initiated",
                "room": room_name,
                "participant_id": participant.participant_id
            }

        except Exception as e:
            logger.error(f"Failed to trigger call: {e}")
            raise e
        finally:
            await lk_api.aclose()
