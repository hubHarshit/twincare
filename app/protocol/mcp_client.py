from typing import Dict, Any, Optional
from .schemas import AgentRequest, AgentResponse
from ..context.manager import ContextManager
from ..agents.base_chat import BaseChatAgent

class MCPClient:
    def __init__(self):
        self.context_manager = ContextManager()
        self.agents: Dict[str, BaseChatAgent] = {
            'base_chat': BaseChatAgent(),
            # Add other agents here
        }
        self._setup_agents()

    def _setup_agents(self):
        """Initialize agents with context manager"""
        for agent in self.agents.values():
            agent.set_context_manager(self.context_manager)

    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """Process request through MCP pipeline"""
        # 1. Context Layer: Get/Update Context
        context = self.context_manager.get_context(request.user_id)
        request.context = context

        # 2. Protocol Layer: Route to appropriate agent
        current_agent = context.get('current_agent', 'base_chat')
        if current_agent not in self.agents:
            raise ValueError(f"Unknown agent: {current_agent}")

        # 3. Model Layer: Process through agent
        agent = self.agents[current_agent]
        response = await agent.process(request)

        # 4. Context Layer: Update context with response
        self.context_manager.update_context(request.user_id, response.updated_context)

        return response

    def register_agent(self, name: str, agent: BaseChatAgent):
        """Register a new agent with the MCP client"""
        agent.set_context_manager(self.context_manager)
        self.agents[name] = agent

    def get_agent(self, name: str) -> Optional[BaseChatAgent]:
        """Get agent by name"""
        return self.agents.get(name)

    def get_context(self, user_id: str) -> Dict[str, Any]:
        """Get context for user"""
        return self.context_manager.get_context(user_id)

    def save_context(self, user_id: str, filepath: str):
        """Save context to file"""
        self.context_manager.save_context(user_id, filepath)

    def load_context(self, user_id: str, filepath: str):
        """Load context from file"""
        self.context_manager.load_context(user_id, filepath) 