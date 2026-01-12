"""
MCP (Model Context Protocol) Client Module

Provides client functionality to connect to external MCP servers and expose their
tools to the LLM for function calling.
"""

from typing import Dict, Any, List, Optional
import asyncio
import json
import os
from dataclasses import dataclass, field
from contextlib import asynccontextmanager


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""
    name: str
    command: str  # e.g., "npx", "python", "node"
    args: List[str] = field(default_factory=list)  # e.g., ["-y", "@modelcontextprotocol/server-filesystem", "/path"]
    env: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class MCPTool:
    """Represents a tool from an MCP server"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str


class MCPClient:
    """Client for connecting to MCP servers via stdio transport"""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.process: Optional[asyncio.subprocess.Process] = None
        self.tools: List[MCPTool] = []
        self._request_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}
        self._read_task: Optional[asyncio.Task] = None
        self._connected = False
    
    async def connect(self) -> bool:
        """Start the MCP server process and initialize connection"""
        try:
            env = os.environ.copy()
            env.update(self.config.env)
            
            self.process = await asyncio.create_subprocess_exec(
                self.config.command,
                *self.config.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            # Start reading responses
            self._read_task = asyncio.create_task(self._read_responses())
            
            # Initialize the connection
            init_result = await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True},
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "MIDAS",
                    "version": "1.0.0"
                }
            })
            
            if init_result:
                # Send initialized notification
                await self._send_notification("notifications/initialized", {})
                self._connected = True
                
                # Fetch available tools
                await self._fetch_tools()
                print(f"✅ MCP server '{self.config.name}' connected with {len(self.tools)} tools")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Failed to connect to MCP server '{self.config.name}': {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        self._connected = False
        
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
        
        if self.process:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()
            self.process = None
        
        self.tools = []
        print(f"🔌 MCP server '{self.config.name}' disconnected")
    
    async def _read_responses(self):
        """Read responses from the MCP server"""
        try:
            while self.process and self.process.stdout:
                line = await self.process.stdout.readline()
                if not line:
                    break
                
                try:
                    message = json.loads(line.decode().strip())
                    
                    # Handle response
                    if "id" in message and message["id"] in self._pending_requests:
                        future = self._pending_requests.pop(message["id"])
                        if "error" in message:
                            future.set_exception(Exception(message["error"].get("message", "Unknown error")))
                        else:
                            future.set_result(message.get("result"))
                    
                except json.JSONDecodeError:
                    continue
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"⚠️ MCP read error for '{self.config.name}': {e}")
    
    async def _send_request(self, method: str, params: Dict[str, Any]) -> Any:
        """Send a JSON-RPC request and wait for response"""
        if not self.process or not self.process.stdin:
            raise Exception("Not connected to MCP server")
        
        self._request_id += 1
        request_id = self._request_id
        
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending_requests[request_id] = future
        
        message = json.dumps(request) + "\n"
        self.process.stdin.write(message.encode())
        await self.process.stdin.drain()
        
        try:
            return await asyncio.wait_for(future, timeout=30.0)
        except asyncio.TimeoutError:
            self._pending_requests.pop(request_id, None)
            raise Exception(f"Request timeout for method '{method}'")
    
    async def _send_notification(self, method: str, params: Dict[str, Any]):
        """Send a JSON-RPC notification (no response expected)"""
        if not self.process or not self.process.stdin:
            return
        
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        
        message = json.dumps(notification) + "\n"
        self.process.stdin.write(message.encode())
        await self.process.stdin.drain()
    
    async def _fetch_tools(self):
        """Fetch available tools from the MCP server"""
        try:
            result = await self._send_request("tools/list", {})
            self.tools = []
            
            for tool_data in result.get("tools", []):
                tool = MCPTool(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    input_schema=tool_data.get("inputSchema", {}),
                    server_name=self.config.name
                )
                self.tools.append(tool)
                
        except Exception as e:
            print(f"⚠️ Failed to fetch tools from '{self.config.name}': {e}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server"""
        if not self._connected:
            raise Exception(f"Not connected to MCP server '{self.config.name}'")
        
        result = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        
        return result
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources from the MCP server"""
        if not self._connected:
            return []
        
        try:
            result = await self._send_request("resources/list", {})
            return result.get("resources", [])
        except Exception as e:
            print(f"⚠️ Failed to list resources from '{self.config.name}': {e}")
            return []
    
    async def read_resource(self, uri: str) -> Any:
        """Read a resource from the MCP server"""
        if not self._connected:
            raise Exception(f"Not connected to MCP server '{self.config.name}'")
        
        result = await self._send_request("resources/read", {"uri": uri})
        return result


class MCPManager:
    """Manages multiple MCP server connections"""
    
    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
        self.configs: List[MCPServerConfig] = []
        self._initialized = False
    
    def load_config_from_file(self, config_path: str = "mcp_servers.json"):
        """Load MCP server configurations from a JSON file"""
        if not os.path.exists(config_path):
            print(f"ℹ️ No MCP config file found at {config_path}")
            return
        
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
            
            self.configs = []
            for server_data in data.get("mcpServers", data.get("servers", [])):
                if isinstance(server_data, dict):
                    # Handle both formats: {"name": ..., "command": ...} or {"serverName": {"command": ...}}
                    if "command" in server_data:
                        config = MCPServerConfig(
                            name=server_data.get("name", "unnamed"),
                            command=server_data["command"],
                            args=server_data.get("args", []),
                            env=server_data.get("env", {}),
                            enabled=server_data.get("enabled", True)
                        )
                        self.configs.append(config)
            
            # Also handle Claude Desktop format: {"mcpServers": {"name": {"command": ...}}}
            if "mcpServers" in data and isinstance(data["mcpServers"], dict):
                for name, server_data in data["mcpServers"].items():
                    if isinstance(server_data, dict) and "command" in server_data:
                        config = MCPServerConfig(
                            name=name,
                            command=server_data["command"],
                            args=server_data.get("args", []),
                            env=server_data.get("env", {}),
                            enabled=server_data.get("enabled", True)
                        )
                        # Avoid duplicates
                        if not any(c.name == name for c in self.configs):
                            self.configs.append(config)
            
            print(f"📋 Loaded {len(self.configs)} MCP server configs")
            
        except Exception as e:
            print(f"❌ Failed to load MCP config: {e}")
    
    def add_server(self, config: MCPServerConfig):
        """Add an MCP server configuration"""
        self.configs.append(config)
    
    async def connect_all(self):
        """Connect to all configured MCP servers"""
        for config in self.configs:
            if not config.enabled:
                continue
            
            if config.name in self.clients:
                continue
            
            try:
                client = MCPClient(config)
                if await client.connect():
                    self.clients[config.name] = client
            except Exception as e:
                print(f"⚠️ Failed to connect to MCP server '{config.name}': {e}")
                # Continue with other servers
        
        self._initialized = True
    
    async def disconnect_all(self):
        """Disconnect from all MCP servers"""
        for client in self.clients.values():
            await client.disconnect()
        self.clients.clear()
        self._initialized = False
    
    async def reconnect(self, server_name: str) -> bool:
        """Reconnect to a specific MCP server"""
        if server_name in self.clients:
            await self.clients[server_name].disconnect()
            del self.clients[server_name]
        
        config = next((c for c in self.configs if c.name == server_name), None)
        if not config:
            return False
        
        client = MCPClient(config)
        if await client.connect():
            self.clients[server_name] = client
            return True
        return False
    
    def get_all_tools(self) -> List[MCPTool]:
        """Get all tools from all connected MCP servers"""
        tools = []
        for client in self.clients.values():
            tools.extend(client.tools)
        return tools
    
    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """Format all MCP tools for LLM function calling"""
        tools = []
        for mcp_tool in self.get_all_tools():
            # Prefix tool name with server name to avoid conflicts
            full_name = f"mcp_{mcp_tool.server_name}_{mcp_tool.name}"
            tools.append({
                "type": "function",
                "function": {
                    "name": full_name,
                    "description": f"[MCP:{mcp_tool.server_name}] {mcp_tool.description}",
                    "parameters": mcp_tool.input_schema
                }
            })
        return tools
    
    async def call_tool(self, full_tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call an MCP tool by its full name (mcp_servername_toolname)"""
        # Parse the tool name
        if not full_tool_name.startswith("mcp_"):
            raise ValueError(f"Invalid MCP tool name: {full_tool_name}")
        
        parts = full_tool_name[4:].split("_", 1)  # Remove "mcp_" prefix
        if len(parts) != 2:
            raise ValueError(f"Invalid MCP tool name format: {full_tool_name}")
        
        server_name, tool_name = parts
        
        if server_name not in self.clients:
            raise ValueError(f"MCP server '{server_name}' not connected")
        
        return await self.clients[server_name].call_tool(tool_name, arguments)
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get status of all MCP servers"""
        return {
            "initialized": self._initialized,
            "servers": [
                {
                    "name": config.name,
                    "enabled": config.enabled,
                    "connected": config.name in self.clients,
                    "tools_count": len(self.clients[config.name].tools) if config.name in self.clients else 0
                }
                for config in self.configs
            ]
        }


# Global MCP manager instance
mcp_manager = MCPManager()


async def initialize_mcp():
    """Initialize MCP connections on startup"""
    try:
        from backend.config import settings
        mcp_manager.load_config_from_file(settings.mcp_config_path)
        await mcp_manager.connect_all()
    except Exception as e:
        print(f"⚠️ MCP initialization failed (non-fatal): {e}")
        # Don't crash the server if MCP fails to initialize


async def shutdown_mcp():
    """Shutdown MCP connections"""
    await mcp_manager.disconnect_all()
