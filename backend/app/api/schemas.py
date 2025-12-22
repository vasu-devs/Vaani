from pydantic import BaseModel

class CallRequest(BaseModel):
    phone_number: str
    debt_amount: int
    debtor_name: str
    agent_name: str = "Rachel"
    agent_voice: str = "asteria"
    user_details: str = ""

class CallResponse(BaseModel):
    status: str
    message: str = ""
    room: str = ""
    participant_id: str = ""
