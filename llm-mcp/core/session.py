# core/session.py

import os
import sys
from typing import Optional, Any, List, Dict
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
try:
    # Optional import for SSE transport
    from mcp.client.sse import sse_client
except Exception:
    sse_client = None


class MCP:
    """
    Lightweight wrapper for one-time MCP tool calls using stdio transport.
    Each call spins up a new subprocess and terminates cleanly.
    """

    def __init__(
        self,
        server_script: str = "mcp_server_2.py",
        working_dir: Optional[str] = None,
        server_command: Optional[str] = None,
    ):
        self.server_script = server_script
        self.working_dir = working_dir or os.getcwd()
        self.server_command = server_command or sys.executable

    async def list_tools(self):
        server_params = StdioServerParameters(
            command=self.server_command,
            args=[self.server_script],
            cwd=self.working_dir
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_result = await session.list_tools()
                return tools_result.tools

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        server_params = StdioServerParameters(
            command=self.server_command,
            args=[self.server_script],
            cwd=self.working_dir
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await session.call_tool(tool_name, arguments=arguments)


class MultiMCP:
    """
    Stateless version: discovers tools from multiple MCP servers, but reconnects per tool call.
    Each call_tool() uses a fresh session based on tool-to-server mapping.
    """

    def __init__(self, server_configs: List[dict]):
        self.server_configs = server_configs
        self.tool_map: Dict[str, Dict[str, Any]] = {}  # tool_name → {config, tool}

    async def initialize(self):
        print("in MultiMCP initialize")
        for config in self.server_configs:
            transport = config.get("transport", "stdio")
            try:
                if transport == "sse":
                    if sse_client is None:
                        print("❌ SSE client not available; install mcp[cli]>=1.6.0")
                        continue
                    url = config.get("url")
                    if not url:
                        print(f"❌ Missing 'url' for SSE server {config.get('id', 'unknown')}")
                        continue
                    print(f"→ Scanning tools from SSE: {url}")
                    async with sse_client(url) as (read, write):
                        try:
                            async with ClientSession(read, write) as session:
                                await session.initialize()
                                tools = await session.list_tools()
                                print(f"→ Tools received: {[tool.name for tool in tools.tools]}")
                                for tool in tools.tools:
                                    self.tool_map[tool.name] = {"config": config, "tool": tool}
                        except Exception as se:
                            print(f"❌ SSE session error: {se}")
                else:
                    params = StdioServerParameters(
                        command=sys.executable,
                        args=[config["script"]],
                        cwd=config.get("cwd", os.getcwd())
                    )
                    print(f"→ Scanning tools from: {config.get('script')} in {params.cwd}")
                    async with stdio_client(params) as (read, write):
                        try:
                            async with ClientSession(read, write) as session:
                                await session.initialize()
                                tools = await session.list_tools()
                                print(f"→ Tools received: {[tool.name for tool in tools.tools]}")
                                for tool in tools.tools:
                                    self.tool_map[tool.name] = {"config": config, "tool": tool}
                        except Exception as se:
                            print(f"❌ Session error: {se}")
            except Exception as e:
                print(f"❌ Error initializing MCP server {config.get('script', config.get('url', 'unknown'))}: {e}")

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        entry = self.tool_map.get(tool_name)
        if not entry:
            raise ValueError(f"Tool '{tool_name}' not found on any server.")

        config = entry["config"]
        transport = config.get("transport", "stdio")

        if transport == "sse":
            if sse_client is None:
                raise RuntimeError("SSE client not available; install mcp[cli]>=1.6.0")
            url = config.get("url")
            if not url:
                raise ValueError("SSE server missing 'url' in config")
            async with sse_client(url) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    return await session.call_tool(tool_name, arguments)
        else:
            params = StdioServerParameters(
                command=sys.executable,
                args=[config["script"]],
                cwd=config.get("cwd", os.getcwd())
            )
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    return await session.call_tool(tool_name, arguments)

    async def list_all_tools(self) -> List[str]:
        return list(self.tool_map.keys())

    def get_all_tools(self) -> List[Any]:
        return [entry["tool"] for entry in self.tool_map.values()]

    async def shutdown(self):
        pass  # no persistent sessions to close