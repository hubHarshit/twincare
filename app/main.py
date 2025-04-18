from fastapi import FastAPI
from .protocol.router import router as agent_router
from .protocol.mcp_client import MCPClient

app = FastAPI(title="Multi-Agent Medical Assistant")

# Initialize MCP client
mcp_client = MCPClient()

# Include routers
app.include_router(agent_router, prefix="/api/v1", tags=["agents"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Multi-Agent Medical Assistant API"} 