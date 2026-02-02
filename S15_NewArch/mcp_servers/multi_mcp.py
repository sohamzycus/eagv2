# multi_mcp.py - S20 Upgraded Multi-MCP Server Manager
# Features: Config-based loading, Git support, Caching, Increased timeout

import asyncio
import sys
import shutil
import json
import subprocess
import os
from pathlib import Path
from contextlib import AsyncExitStack
from datetime import datetime
from typing import Dict, List, Optional, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool
from rich import print


class MultiMCP:
    """
    S20 Upgraded Multi-MCP Server Manager
    
    Features:
    - Config file-based server loading (mcp_config.json)
    - Git repository support for dynamic server installation
    - File-based caching (mcp_cache.json)
    - Increased timeout (20s default, prevents flaky connections)
    - Graceful error handling and retries
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.exit_stack = AsyncExitStack()
        self.sessions: Dict[str, ClientSession] = {}
        self.tools: Dict[str, List[Tool]] = {}
        self.tool_cache: Dict[str, Any] = {}
        
        # Load config
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "mcp_config.json"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Cache settings
        self.cache_enabled = self.config.get("global_settings", {}).get("cache_enabled", True)
        self.cache_file = Path(__file__).parent / self.config.get("global_settings", {}).get("cache_file", "mcp_cache.json")
        
        # Load cache if exists
        if self.cache_enabled and self.cache_file.exists():
            try:
                self.tool_cache = json.loads(self.cache_file.read_text())
                print(f"[dim]📦 Loaded tool cache: {len(self.tool_cache)} entries[/dim]")
            except Exception as e:
                print(f"[yellow]⚠️ Failed to load cache: {e}[/yellow]")
    
    def _load_config(self) -> dict:
        """Load MCP configuration from JSON file"""
        if self.config_path.exists():
            try:
                config = json.loads(self.config_path.read_text())
                print(f"[green]✅ Loaded MCP config from {self.config_path}[/green]")
                return config
            except Exception as e:
                print(f"[yellow]⚠️ Failed to load config: {e}. Using defaults.[/yellow]")
        
        # Fallback to hardcoded defaults (for backwards compatibility)
        return {
            "servers": {
                "browser": {
                    "command": "uv",
                    "args": ["run", "S15_NewArch/mcp_servers/server_browser.py"],
                    "timeout": 20,
                    "enabled": True
                },
                "rag": {
                    "command": "uv",
                    "args": ["run", "S15_NewArch/mcp_servers/server_rag.py"],
                    "timeout": 30,
                    "enabled": True
                },
                "sandbox": {
                    "command": "uv",
                    "args": ["run", "S15_NewArch/mcp_servers/server_sandbox.py"],
                    "timeout": 60,
                    "enabled": True
                }
            },
            "global_settings": {
                "default_timeout": 20,
                "max_retries": 3
            }
        }
    
    def _save_cache(self):
        """Save tool cache to file"""
        if self.cache_enabled:
            try:
                self.cache_file.write_text(json.dumps(self.tool_cache, indent=2, default=str))
            except Exception as e:
                print(f"[yellow]⚠️ Failed to save cache: {e}[/yellow]")
    
    async def _install_git_server(self, git_url: str, target_dir: Path) -> bool:
        """
        Clone and install a server from a Git URL.
        
        Example git_url: "https://github.com/user/mcp-server.git"
        """
        try:
            if target_dir.exists():
                print(f"[dim]📁 Server already installed at {target_dir}[/dim]")
                return True
            
            print(f"[cyan]📥 Cloning {git_url}...[/cyan]")
            
            # Clone repository
            result = subprocess.run(
                ["git", "clone", git_url, str(target_dir)],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                print(f"[red]❌ Git clone failed: {result.stderr}[/red]")
                return False
            
            # Install dependencies if requirements.txt exists
            requirements_file = target_dir / "requirements.txt"
            if requirements_file.exists():
                print(f"[cyan]📦 Installing dependencies...[/cyan]")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                    capture_output=True,
                    timeout=300
                )
            
            print(f"[green]✅ Server installed at {target_dir}[/green]")
            return True
            
        except Exception as e:
            print(f"[red]❌ Git installation failed: {e}[/red]")
            return False

    async def start(self):
        """Start all configured servers with improved timeout and error handling"""
        print("[bold green]🚀 Starting MCP Servers...[/bold green]")
        
        servers_config = self.config.get("servers", {})
        global_settings = self.config.get("global_settings", {})
        default_timeout = global_settings.get("default_timeout", 20)
        max_retries = global_settings.get("max_retries", 3)
        
        for name, config in servers_config.items():
            # Skip disabled servers
            if not config.get("enabled", True):
                print(f"  ⏭️ [dim]{name}[/dim] (disabled)")
                continue
            
            # Handle git-based servers
            if "git_url" in config:
                install_dir = Path(__file__).parent / "installed" / name
                if not await self._install_git_server(config["git_url"], install_dir):
                    print(f"  ❌ [red]{name}[/red] installation failed")
                    continue
                # Update command to use installed server
                config["args"] = [str(install_dir / config.get("entry_point", "server.py"))]
            
            # Retry logic for flaky connections
            for attempt in range(1, max_retries + 1):
                try:
                    # Check if uv exists, else fallback to python
                    cmd = config.get("command", "uv")
                    args = config.get("args", [])
                    
                    if cmd == "uv" and not shutil.which("uv"):
                        cmd = sys.executable
                        # Extract just the script path for python execution
                        if args and len(args) > 1:
                            args = [args[-1]]  # Just the script path
                    
                    # Server timeout from config (increased default: 20s)
                    timeout = config.get("timeout", default_timeout)

                    server_params = StdioServerParameters(
                        command=cmd,
                        args=args,
                        env=None 
                    )
                    
                    # Connect with timeout
                    read, write = await asyncio.wait_for(
                        self.exit_stack.enter_async_context(stdio_client(server_params)),
                        timeout=timeout
                    )
                    session = await self.exit_stack.enter_async_context(ClientSession(read, write))
                    
                    # Initialize with timeout
                    await asyncio.wait_for(session.initialize(), timeout=timeout)
                    
                    # List tools
                    result = await asyncio.wait_for(session.list_tools(), timeout=timeout)
                    self.sessions[name] = session
                    self.tools[name] = result.tools
                    
                    # Cache tool info
                    self.tool_cache[name] = {
                        "tools": [{"name": t.name, "description": t.description} for t in result.tools],
                        "last_connected": datetime.now().isoformat()
                    }
                    
                    print(f"  ✅ [cyan]{name}[/cyan] connected. Tools: {len(result.tools)}")
                    break  # Success, exit retry loop
                    
                except asyncio.TimeoutError:
                    print(f"  ⚠️ [yellow]{name}[/yellow] timeout (attempt {attempt}/{max_retries})")
                    if attempt == max_retries:
                        print(f"  ❌ [red]{name}[/red] failed after {max_retries} attempts")
                        
                except Exception as e:
                    print(f"  ⚠️ [yellow]{name}[/yellow] error: {e} (attempt {attempt}/{max_retries})")
                    if attempt == max_retries:
                        print(f"  ❌ [red]{name}[/red] failed: {e}")
        
        # Save cache after all connections
        self._save_cache()
        
        print(f"[bold green]✅ MCP Servers ready: {len(self.sessions)} connected[/bold green]")

    async def stop(self):
        """Stop all servers"""
        print("[bold yellow]🛑 Stopping MCP Servers...[/bold yellow]")
        self._save_cache()
        await self.exit_stack.aclose()

    def get_all_tools(self) -> list:
        """Get all tools from all connected servers"""
        all_tools = []
        for tools in self.tools.values():
            all_tools.extend(tools)
        return all_tools

    async def function_wrapper(self, tool_name: str, *args):
        """Execute a tool using positional arguments by mapping them to schema keys"""
        # Find tool definition
        target_tool = None
        for tools in self.tools.values():
            for tool in tools:
                if tool.name == tool_name:
                    target_tool = tool
                    break
            if target_tool: break
        
        if not target_tool:
            return f"Error: Tool {tool_name} not found"

        # Map positional args to keyword args based on schema
        arguments = {}
        schema = target_tool.inputSchema
        if schema and 'properties' in schema:
            keys = list(schema['properties'].keys())
            for i, arg in enumerate(args):
                if i < len(keys):
                    arguments[keys[i]] = arg
        
        try:
            result = await self.route_tool_call(tool_name, arguments)
            # Unpack CallToolResult
            if hasattr(result, 'content') and result.content:
                return result.content[0].text
            return str(result)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def get_tools_from_servers(self, server_names: list) -> list:
        """Get flattened list of tools from requested servers"""
        all_tools = []
        for name in server_names:
            if name in self.tools:
                all_tools.extend(self.tools[name])
        return all_tools

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict):
        """Call a tool on a specific server with timeout"""
        if server_name not in self.sessions:
            raise ValueError(f"Server '{server_name}' not connected")
        
        # Get timeout from config
        timeout = self.config.get("servers", {}).get(server_name, {}).get("timeout", 20)
        
        try:
            return await asyncio.wait_for(
                self.sessions[server_name].call_tool(tool_name, arguments),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"Tool '{tool_name}' on server '{server_name}' timed out after {timeout}s")

    async def route_tool_call(self, tool_name: str, arguments: dict):
        """Route tool call to appropriate server"""
        for name, tools in self.tools.items():
            for tool in tools:
                if tool.name == tool_name:
                    return await self.call_tool(name, tool_name, arguments)
        raise ValueError(f"Tool '{tool_name}' not found in any server")
    
    def get_server_status(self) -> dict:
        """Get status of all servers"""
        status = {}
        for name, config in self.config.get("servers", {}).items():
            status[name] = {
                "enabled": config.get("enabled", True),
                "connected": name in self.sessions,
                "tools_count": len(self.tools.get(name, [])),
                "cached_at": self.tool_cache.get(name, {}).get("last_connected")
            }
        return status