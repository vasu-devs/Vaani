import re
from pydantic import BaseModel, field_validator

class CallRequest(BaseModel):
    phone_number: str
    debt_amount: float
    debtor_name: str
    agent_name: str = "Rachel"
    agent_voice: str = "asteria"
    user_details: str = ""

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r"[\s\-\(\)]", "", v)
        if not re.match(r"^\+?[1-9]\d{6,14}$", cleaned):
            raise ValueError("Invalid phone number format. Use E.164 (e.g. +15550000000)")
        return cleaned

class CallResponse(BaseModel):
    status: str
    message: str = ""
    room: str = ""
    participant_id: str = ""
