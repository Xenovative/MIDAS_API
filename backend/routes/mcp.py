"""
MCP (Model Context Protocol) API Routes

Provides endpoints for managing MCP server connections and tools.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from backend.mcp_client import mcp_manager, MCPServerConfig

router = APIRouter(prefix="/mcp", tags=["mcp"])


class MCPServerCreate(BaseModel):
    name: str
    command: str
    args: List[str] = []
    env: Dict[str, str] = {}
    enabled: bool = True


class MCPToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = {}


@router.get("/status")
async def get_mcp_status():
    """Get status of all MCP servers"""
    return mcp_manager.get_server_status()


@router.get("/servers")
async def list_servers():
    """List all configured MCP servers"""
    return {
        "servers": [
            {
                "name": config.name,
                "command": config.command,
                "args": config.args,
                "enabled": config.enabled,
                "connected": config.name in mcp_manager.clients
            }
            for config in mcp_manager.configs
        ]
    }


@router.post("/servers")
async def add_server(server: MCPServerCreate):
    """Add a new MCP server configuration"""
    # Check if server with same name exists
    if any(c.name == server.name for c in mcp_manager.configs):
        raise HTTPException(status_code=400, detail=f"Server '{server.name}' already exists")
    
    config = MCPServerConfig(
        name=server.name,
        command=server.command,
        args=server.args,
        env=server.env,
        enabled=server.enabled
    )
    
    mcp_manager.add_server(config)
    
    # Try to connect if enabled
    if server.enabled:
        from backend.mcp_client import MCPClient
        client = MCPClient(config)
        if await client.connect():
            mcp_manager.clients[server.name] = client
            return {"status": "connected", "tools_count": len(client.tools)}
        else:
            return {"status": "added_but_not_connected", "message": "Server added but failed to connect"}
    
    return {"status": "added", "enabled": False}


@router.post("/servers/{server_name}/connect")
async def connect_server(server_name: str):
    """Connect to a specific MCP server"""
    if await mcp_manager.reconnect(server_name):
        client = mcp_manager.clients.get(server_name)
        return {
            "status": "connected",
            "tools_count": len(client.tools) if client else 0
        }
    raise HTTPException(status_code=500, detail=f"Failed to connect to server '{server_name}'")


@router.post("/servers/{server_name}/disconnect")
async def disconnect_server(server_name: str):
    """Disconnect from a specific MCP server"""
    if server_name not in mcp_manager.clients:
        raise HTTPException(status_code=404, detail=f"Server '{server_name}' not connected")
    
    await mcp_manager.clients[server_name].disconnect()
    del mcp_manager.clients[server_name]
    
    return {"status": "disconnected"}


@router.delete("/servers/{server_name}")
async def remove_server(server_name: str):
    """Remove an MCP server configuration"""
    # Disconnect if connected
    if server_name in mcp_manager.clients:
        await mcp_manager.clients[server_name].disconnect()
        del mcp_manager.clients[server_name]
    
    # Remove from configs
    mcp_manager.configs = [c for c in mcp_manager.configs if c.name != server_name]
    
    return {"status": "removed"}


@router.get("/tools")
async def list_tools():
    """List all available MCP tools"""
    tools = mcp_manager.get_all_tools()
    return {
        "tools": [
            {
                "name": tool.name,
                "full_name": f"mcp_{tool.server_name}_{tool.name}",
                "description": tool.description,
                "server": tool.server_name,
                "input_schema": tool.input_schema
            }
            for tool in tools
        ]
    }


@router.get("/tools/llm")
async def get_tools_for_llm():
    """Get MCP tools formatted for LLM function calling"""
    return {"tools": mcp_manager.get_tools_for_llm()}


@router.post("/tools/call")
async def call_tool(request: MCPToolCall):
    """Call an MCP tool directly"""
    try:
        result = await mcp_manager.call_tool(request.tool_name, request.arguments)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers/{server_name}/resources")
async def list_resources(server_name: str):
    """List resources from a specific MCP server"""
    if server_name not in mcp_manager.clients:
        raise HTTPException(status_code=404, detail=f"Server '{server_name}' not connected")
    
    resources = await mcp_manager.clients[server_name].list_resources()
    return {"resources": resources}


@router.post("/servers/{server_name}/resources/read")
async def read_resource(server_name: str, uri: str):
    """Read a resource from a specific MCP server"""
    if server_name not in mcp_manager.clients:
        raise HTTPException(status_code=404, detail=f"Server '{server_name}' not connected")
    
    try:
        result = await mcp_manager.clients[server_name].read_resource(uri)
        return {"success": True, "content": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
