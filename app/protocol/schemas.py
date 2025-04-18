from pydantic import BaseModel
from typing import Optional, Dict, Any

class AgentRequest(BaseModel):
    user_id: str
    input_text: str
    context: Dict[str, Any]

class AgentResponse(BaseModel):
    response_text: str
    updated_context: Dict[str, Any]
    next_agent: Optional[str] = None
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None 