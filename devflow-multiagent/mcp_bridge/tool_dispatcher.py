"""
MCP Bridge - Tool Dispatcher for External Tools

This module bridges DevFlow with MCP (Model Context Protocol) servers.
Allows dispatching tool calls to external processes.

NOTE: This can use existing MCP infrastructure when needed.
"""

import asyncio
import json
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class ToolStatus(Enum):
    """Status of tool execution."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"


@dataclass
class ToolResult:
    """Result of a tool execution."""
    tool_name: str
    status: ToolStatus
    output: Any
    error: Optional[str] = None
    execution_time_ms: int = 0


@dataclass
class ToolDefinition:
    """Definition of an available tool."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema for parameters
    handler: Optional[Callable] = None  # For local tools


class ToolDispatcher:
    """
    Dispatches tool calls to appropriate handlers.
    
    Supports:
    - Local Python functions
    - External MCP servers (when configured)
    - CLI command wrappers
    """
    
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.mcp_servers: Dict[str, Dict] = {}
        
        # Register built-in tools
        self._register_builtins()
    
    def _register_builtins(self):
        """Register built-in DevFlow tools."""
        
        # Git tools
        self.register_tool(ToolDefinition(
            name="git_commits",
            description="Get recent git commits",
            parameters={
                "type": "object",
                "properties": {
                    "since": {"type": "string", "description": "Start date"},
                    "limit": {"type": "integer", "default": 20}
                }
            },
            handler=self._handle_git_commits
        ))
        
        self.register_tool(ToolDefinition(
            name="git_diff",
            description="Get git diff statistics",
            parameters={
                "type": "object",
                "properties": {
                    "ref": {"type": "string", "description": "Reference to diff against"}
                }
            },
            handler=self._handle_git_diff
        ))
        
        # File tools
        self.register_tool(ToolDefinition(
            name="read_file",
            description="Read contents of a file",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"}
                },
                "required": ["path"]
            },
            handler=self._handle_read_file
        ))
        
        self.register_tool(ToolDefinition(
            name="list_files",
            description="List files in a directory",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "default": "."},
                    "pattern": {"type": "string", "description": "Glob pattern"}
                }
            },
            handler=self._handle_list_files
        ))
        
        # Analysis tools
        self.register_tool(ToolDefinition(
            name="analyze_code",
            description="Analyze code for quality metrics",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File to analyze"}
                },
                "required": ["path"]
            },
            handler=self._handle_analyze_code
        ))
    
    def register_tool(self, tool: ToolDefinition):
        """Register a new tool."""
        self.tools[tool.name] = tool
    
    def register_mcp_server(self, server_id: str, config: Dict):
        """
        Register an external MCP server.
        
        Args:
            server_id: Unique identifier for server
            config: Server configuration (script, cwd, etc.)
        """
        self.mcp_servers[server_id] = config
    
    async def dispatch(
        self, 
        tool_name: str, 
        parameters: Dict = None,
        timeout: int = 30
    ) -> ToolResult:
        """
        Dispatch a tool call.
        
        Args:
            tool_name: Name of tool to call
            parameters: Tool parameters
            timeout: Timeout in seconds
        
        Returns:
            ToolResult with output or error
        """
        import time
        start = time.time()
        
        tool = self.tools.get(tool_name)
        
        if not tool:
            return ToolResult(
                tool_name=tool_name,
                status=ToolStatus.NOT_FOUND,
                output=None,
                error=f"Tool not found: {tool_name}"
            )
        
        try:
            if tool.handler:
                # Local handler
                result = await asyncio.wait_for(
                    tool.handler(parameters or {}),
                    timeout=timeout
                )
                
                elapsed = int((time.time() - start) * 1000)
                
                return ToolResult(
                    tool_name=tool_name,
                    status=ToolStatus.SUCCESS,
                    output=result,
                    execution_time_ms=elapsed
                )
            else:
                # No handler available
                return ToolResult(
                    tool_name=tool_name,
                    status=ToolStatus.ERROR,
                    output=None,
                    error="No handler configured for tool"
                )
                
        except asyncio.TimeoutError:
            return ToolResult(
                tool_name=tool_name,
                status=ToolStatus.TIMEOUT,
                output=None,
                error=f"Tool timed out after {timeout}s"
            )
        except Exception as e:
            return ToolResult(
                tool_name=tool_name,
                status=ToolStatus.ERROR,
                output=None,
                error=str(e)
            )
    
    def list_tools(self) -> List[Dict]:
        """List all available tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools.values()
        ]
    
    # ==================== Built-in Handlers ====================
    
    async def _handle_git_commits(self, params: Dict) -> Dict:
        """Handle git_commits tool."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", "log",
                f"--since={params.get('since', 'yesterday')}",
                "--pretty=format:%h|%s|%an",
                f"-n{params.get('limit', 20)}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            
            commits = []
            for line in stdout.decode().strip().split("\n"):
                parts = line.split("|")
                if len(parts) >= 3:
                    commits.append({
                        "hash": parts[0],
                        "message": parts[1],
                        "author": parts[2]
                    })
            
            return {"commits": commits, "count": len(commits)}
        except Exception as e:
            return {"error": str(e), "commits": []}
    
    async def _handle_git_diff(self, params: Dict) -> Dict:
        """Handle git_diff tool."""
        try:
            ref = params.get("ref", "HEAD~5")
            
            proc = await asyncio.create_subprocess_exec(
                "git", "diff", "--stat", ref,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            
            return {"diff": stdout.decode().strip()}
        except Exception as e:
            return {"error": str(e)}
    
    async def _handle_read_file(self, params: Dict) -> Dict:
        """Handle read_file tool."""
        from pathlib import Path
        
        path = Path(params["path"])
        
        if not path.exists():
            return {"error": "File not found", "content": None}
        
        try:
            content = path.read_text()
            return {
                "content": content,
                "lines": len(content.split("\n")),
                "size": len(content)
            }
        except Exception as e:
            return {"error": str(e), "content": None}
    
    async def _handle_list_files(self, params: Dict) -> Dict:
        """Handle list_files tool."""
        from pathlib import Path
        
        path = Path(params.get("path", "."))
        pattern = params.get("pattern", "*")
        
        try:
            files = list(path.glob(pattern))
            return {
                "files": [str(f) for f in files[:50]],
                "count": len(files)
            }
        except Exception as e:
            return {"error": str(e), "files": []}
    
    async def _handle_analyze_code(self, params: Dict) -> Dict:
        """Handle analyze_code tool."""
        from pathlib import Path
        
        path = Path(params["path"])
        
        if not path.exists():
            return {"error": "File not found"}
        
        try:
            content = path.read_text()
            lines = content.split("\n")
            
            return {
                "file": str(path),
                "lines": len(lines),
                "blank_lines": sum(1 for l in lines if not l.strip()),
                "comment_lines": sum(1 for l in lines if l.strip().startswith("#")),
                "imports": sum(1 for l in lines if l.strip().startswith(("import", "from")))
            }
        except Exception as e:
            return {"error": str(e)}

