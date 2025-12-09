from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
import glob
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CallRequest(BaseModel):
    phone_number: str
    debt_amount: int
    debtor_name: str
    agent_name: str = "Rachel"
    agent_voice: str = "asteria"
    user_details: str = ""

@app.post("/api/call")
async def trigger_call(request: CallRequest):
    """
    Triggers the outbound call script.
    """
    try:
        # We start the process in the background
        # Note: In production, use a task queue like Celery.
        # Here we just run the script.
        # We pass phone number as arg. The other details would normally be passed 
        # via env vars or args to a more complex script. 
        # For now, trigger_call.py only accepts phone number.
        
        # We could modify trigger_call.py to accept more args, or set env vars here.
        env = os.environ.copy()
        env["DEBT_AMOUNT"] = str(request.debt_amount)
        env["DEBTOR_NAME"] = request.debtor_name
        env["AGENT_NAME"] = request.agent_name
        env["AGENT_VOICE"] = request.agent_voice
        env["USER_DETAILS"] = request.user_details
        
        subprocess.Popen(
            [".venv/Scripts/python", "trigger_call.py", request.phone_number],
            env=env,
            cwd=os.getcwd()
        )
        return {"status": "initiated", "message": f"Calling {request.phone_number}..."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
async def get_history():
    """
    Returns list of call logs.
    """
    logs = []
    log_files = glob.glob("call_logs/*.json")
    # Sort by time desc
    log_files.sort(key=os.path.getmtime, reverse=True)
    
    for log_file in log_files:
        try:
            with open(log_file, "r") as f:
                data = json.load(f)
                logs.append({
                    "id": data.get("id"),
                    "timestamp": data.get("timestamp"),
                    "risk_score": data.get("risk_score"),
                    "status": data.get("status")
                })
        except:
            continue
    return logs

@app.get("/api/logs/{log_id}")
async def get_log(log_id: str):
    """
    Returns full details of a log.
    Expects log_id to partially match filename or be the ID.
    We'll search for file containing that ID or timestamp.
    """
    # log_id format usually "call-2023..." or just "2023..."
    # Filename format: log_2023...json
    
    # Try to find file
    # If log_id is "call-20241209_001500", timestamp is "20241209_001500"
    timestamp = log_id.replace("call-", "")
    filename = f"call_logs/log_{timestamp}.json"
    
    if not os.path.exists(filename):
         # Try glob in case format differs
         matches = glob.glob(f"call_logs/*{timestamp}*.json")
         if matches:
             filename = matches[0]
         else:
            raise HTTPException(status_code=404, detail="Log not found")
            
    with open(filename, "r") as f:
        return json.load(f)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
