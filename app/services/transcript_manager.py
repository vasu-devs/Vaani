import os
import json
import logging
import asyncio
from datetime import datetime
from livekit.agents.voice import Agent as VoicePipelineAgent
from app.services.risk_analysis import RiskAnalyzer

logger = logging.getLogger("debt-collector.transcript")

class TranscriptManager:
    def __init__(self):
        self._is_saved = False
        self.risk_analyzer = RiskAnalyzer()

    async def save_transcript(self, agent: VoicePipelineAgent, chat_ctx, metadata: dict):
        """
        Saves the transcript and performs risk analysis.
        Idempotent: Ensures it only runs once per instance if managed correctly.
        """
        if self._is_saved:
            return
        self._is_saved = True
        
        try:
            os.makedirs("call_logs", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"call_logs/log_{timestamp}.json"
            
            transcript = []
            full_text = []
            
            # Access messages
            messages = []
            if hasattr(chat_ctx, "messages"):
                messages = chat_ctx.messages
            elif hasattr(chat_ctx, "_items"):
                messages = chat_ctx._items
            else:
                try:
                    messages = list(chat_ctx)
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
                analysis_result = await self.risk_analyzer.analyze(transcript_text, metadata)
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
