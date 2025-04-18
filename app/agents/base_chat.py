import torch
from datetime import datetime
from transformers import pipeline
from ..protocol.schemas import AgentRequest, AgentResponse
from typing import Dict, Any

class BaseChatAgent:
    def __init__(self):
        self.model = pipeline(
            "text-generation",
            model="gpt2",  # Replace with MedPaLM when available
            device=0 if torch.cuda.is_available() else -1
        )
        self.context_manager = None

    async def process(self, request: AgentRequest) -> AgentResponse:
        # Generate response using the model
        response = self.model(
            request.input_text,
            max_length=100,
            num_return_sequences=1
        )[0]['generated_text']

        # Update context with the interaction
        updated_context = request.context.copy()
        updated_context['last_interaction'] = {
            'input': request.input_text,
            'response': response,
            'timestamp': datetime.now().isoformat()
        }

        return AgentResponse(
            response_text=response,
            updated_context=updated_context,
            confidence=0.8  # Placeholder confidence score
        )

    def set_context_manager(self, context_manager):
        self.context_manager = context_manager 