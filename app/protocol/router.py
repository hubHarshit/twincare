from fastapi import APIRouter, HTTPException
from .schemas import AgentRequest, AgentResponse
from .mcp_client import MCPClient

router = APIRouter()
mcp_client = MCPClient()

@router.post("/route")
async def route_request(request: AgentRequest) -> AgentResponse:
    try:
        return await mcp_client.process_request(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 