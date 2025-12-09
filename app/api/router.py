import glob
import json
import os
import logging
from fastapi import APIRouter, HTTPException
from app.api.schemas import CallRequest, CallResponse
from app.services.sip_handler import SIPHandler

router = APIRouter()
logger = logging.getLogger("debt-collector.api")

@router.post("/call", response_model=CallResponse)
async def trigger_call(request: CallRequest):
    """
    Triggers the outbound call script.
    """
    try:
        # Convert Pydantic to dict
        metadata = request.model_dump(exclude={"phone_number"})
        # Convert int/decimals to string for metadata
        metadata["debt_amount"] = str(metadata["debt_amount"])
        
        result = await SIPHandler.trigger_call(request.phone_number, metadata)
        
        return CallResponse(
            status="initiated", 
            message=f"Calling {request.phone_number}...",
            room=result["room"],
            participant_id=result["participant_id"]
        )
    except Exception as e:
        logger.error(f"API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_history():
    """
    Returns list of call logs.
    """
    logs = []
    # Assumes call_logs is in root
    log_files = glob.glob("call_logs/*.json")
    log_files.sort(key=os.path.getmtime, reverse=True)
    
    for log_file in log_files:
        try:
            with open(log_file, "r") as f:
                data = json.load(f)
                metadata = data.get("metadata", {})
                debtor = metadata.get("debtor_name") or data.get("debtor_name") or "John Doe"

                logs.append({
                    "id": data.get("id"),
                    "timestamp": data.get("timestamp"),
                    "risk_score": data.get("risk_score"),
                    "status": data.get("status"),
                    "debtor_name": debtor
                })
        except:
            continue
    return logs

@router.get("/logs/{log_id}")
async def get_log(log_id: str):
    """
    Returns full details of a log.
    Expects log_id to partially match filename or be the ID.
    """
    timestamp = log_id.replace("call-", "")
    filename = f"call_logs/log_{timestamp}.json"
    
    if not os.path.exists(filename):
         matches = glob.glob(f"call_logs/*{timestamp}*.json")
         if matches:
             filename = matches[0]
         else:
            raise HTTPException(status_code=404, detail="Log not found")
            
    with open(filename, "r") as f:
        return json.load(f)
