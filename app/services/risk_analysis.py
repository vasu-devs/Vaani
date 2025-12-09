import logging
import json
import re
from typing import Literal, Optional
from pydantic import BaseModel, Field
from livekit.agents import llm
from livekit.plugins import groq

logger = logging.getLogger("debt-collector.risk")

# Define nested models for the new schema
class FinancialProfile(BaseModel):
    employed: Optional[bool] = None
    hardship_reason: Optional[str] = None
    payment_method_mentioned: Literal["Credit Card", "Bank Transfer", "None"]

class LegalFlags(BaseModel):
    bankruptcy_risk: bool
    attorney_represented: bool
    cease_and_desist: bool
    dispute_raised: bool

class NegotiationDetails(BaseModel):
    promised_amount: Optional[float] = None
    promised_date: Optional[str] = None

class SherlockRiskAssessment(BaseModel):
    rpc_status: Literal["Yes", "No", "Voicemail"]
    call_outcome: Literal["PTP", "Refusal", "Dispute", "Hangup", "Callback_Requested"]
    risk_score: int = Field(description="0-100 score, 100 is highest risk")
    matrix_quadrant: Literal["Strategic Defaulter", "Hardship", "Forgetful", "Broken Promise", "Unclear"]
    financial_profile: FinancialProfile
    legal_flags: LegalFlags
    negotiation_details: NegotiationDetails
    agent_notes: str = Field(description="Tactical summary for the next collector")

class RiskAnalyzer:
    def __init__(self):
        # Using Groq's Llama 3 70B for deep analysis
        self.analysis_llm = groq.LLM(model="llama-3.3-70b-versatile") 

    async def analyze(self, transcript_text: str, metadata: dict) -> dict:
        logger.info("Starting 'Sherlock' Risk & Compliance Analysis...")
        logger.info(f"Analyzing transcript of length: {len(transcript_text)}")

        # The "Sherlock" Prompt
        sherlock_prompt = f"""
You are **"Sherlock," a Senior Risk & Quality Assurance Officer** for a top-tier debt collection agency. 
Your task is to analyze a transcript of a call between an AI Voice Agent and a Debtor.

Your goal is to **profile the debtor** for future recovery strategy.

### INPUT DATA
- **Debtor Name:** {metadata.get('debtor_name', 'Unknown')}
- **Outstanding Balance:** {metadata.get('debt_amount', 'Unknown')}
- **Transcript:** 
{transcript_text}

### ANALYSIS FRAMEWORK

**STEP 1: IDENTITY VERIFICATION (RPC Check)**
- Did the user confirm they are {metadata.get('debtor_name', 'the debtor')}?
- If this was a voicemail, wrong number, or immediate hangup, mark status as "No Contact".

**STEP 2: THE RISK MATRIX (Willingness vs. Ability)**
Analyze the debtor's statements to place them in one of four quadrants:
1.  **Strategic Defaulter (High Risk):** Has money (Ability: High) but refuses to pay (Willingness: Low). Look for anger, entitlement, or "sue me" comments.
2.  **Hardship Case (Medium Risk):** Wants to pay (Willingness: High) but has no money (Ability: Low). Look for mentions of job loss, medical bills, or bankruptcy.
3.  **Forgetful/Technical (Low Risk):** Has money and wants to pay. Just forgot or had a card error.
4.  **Broken Promise (High Risk):** Feigns willingness but makes vague, non-committal promises to get off the phone.

**STEP 3: COMPLIANCE & LEGAL RED FLAGS (FDCPA)**
Scan strictly for these legal triggers:
- **Bankruptcy:** Did they mention filing for Chapter 7 or 13? (Immediate Stop)
- **Cease & Desist:** Did they say "Stop calling me" or "Don't call me at work"?
- **Disputes:** Did they claim the debt isn't theirs or the amount is wrong?
- **Attorney Rep:** Did they say "Talk to my lawyer"?

**STEP 4: NEGOTIATION OUTCOME**
- **PTP (Promise to Pay):** Did they agree to a *specific* date and amount? (Vague promises don't count).
- **Refusal:** Explicitly stated they will not pay.
- **Stall:** "Call me next week," "I'm driving," etc.

### OUTPUT SCHEMA (JSON ONLY)
Return a valid JSON object with no markdown formatting. The JSON must match this structure exactly:
{{
  "rpc_status": "Yes" | "No" | "Voicemail",
  "call_outcome": "PTP" | "Refusal" | "Dispute" | "Hangup" | "Callback_Requested",
  "risk_score": (Integer 0-100, where 100 is uncollectible/hostile),
  "matrix_quadrant": "Strategic Defaulter" | "Hardship" | "Forgetful" | "Broken Promise" | "Unclear",
  "financial_profile": {{
    "employed": boolean | null,
    "hardship_reason": "string (e.g., 'Unemployment') or null",
    "payment_method_mentioned": "Credit Card" | "Bank Transfer" | "None"
  }},
  "legal_flags": {{
    "bankruptcy_risk": boolean,
    "attorney_represented": boolean,
    "cease_and_desist": boolean,
    "dispute_raised": boolean
  }},
  "negotiation_details": {{
    "promised_amount": float | null,
    "promised_date": "YYYY-MM-DD" | null
  }},
  "agent_notes": "A 1-sentence tactical summary for the next human collector."
}}
"""

        try:
            chat_ctx = llm.ChatContext()
            
            # System prompt to enforce behavior
            system_msg = "You are a specialized Risk Analysis AI. Your ONLY output is valid JSON matching the schema. Do not speak. Do not explain. Do not use Markdown."
            chat_ctx.add_message(role="system", content=system_msg)
            
            chat_ctx.add_message(role="user", content=sherlock_prompt)

            # LiveKit LLM chat returns a stream
            stream = self.analysis_llm.chat(chat_ctx=chat_ctx)
            
            full_text = ""
            async for chunk in stream:
                if chunk.delta and chunk.delta.content:
                    full_text += chunk.delta.content
            
            logger.info(f"Sherlock Raw Output: {full_text}")

            # 3. Clean and Validate
            clean_text = re.sub(r"```json|```", "", full_text).strip()
            
            # Extract JSON if surrounded by text
            json_match = re.search(r"\{.*\}", clean_text, re.DOTALL)
            if json_match:
                clean_text = json_match.group(0)

            # Load into Pydantic
            data_dict = json.loads(clean_text)
            assessment = SherlockRiskAssessment(**data_dict)
            
            result = assessment.model_dump()
            
            # Logic for "Brownie Points" / Auto-Tags
            # We can perform these checks here or return flags for the caller to handle.
            # Adding a 'tags' list to the result for easy consumption.
            tags = []
            if result['risk_score'] >= 80:
                tags.append("High Risk")
            if result['matrix_quadrant'] == "Strategic Defaulter":
                tags.append("Legal Review")
            elif result['matrix_quadrant'] == "Hardship":
                tags.append("Settlement Offer")
            
            if result['legal_flags']['bankruptcy_risk']:
                tags.append("DNC - Bankruptcy")
                logger.warning(f"⛔ AUTO-COMPLIANCE: Bankruptcy flag detected for {metadata.get('debtor_name')}")
            
            result['generated_tags'] = tags
            
            return result

        except Exception as e:
            logger.error(f"Sherlock Analysis Failed: {e}")
            return {
                "risk_score": 50, 
                "agent_notes": f"Analysis Failed: {str(e)}", 
                "call_outcome": "Error",
                "matrix_quadrant": "Unclear"
            }
