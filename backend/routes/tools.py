from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from backend.agent_tools import agent_tool_manager

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("/")
async def list_tools():
    """List all available agent tools"""
    return agent_tool_manager.get_all_tools()


@router.post("/{tool_name}")
async def execute_tool(tool_name: str, parameters: Dict[str, Any]):
    """Execute a specific tool"""
    tool = agent_tool_manager.get_tool(tool_name)
    
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    try:
        result = await tool.execute(**parameters)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
