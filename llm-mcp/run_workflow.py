import os
import asyncio
from core.session import MCP


async def main():
    to_email = os.getenv("GMAIL_DEFAULT_TO")
    mcp = MCP(server_script="mcp_server_workflows.py", working_dir=os.path.dirname(__file__))
    args = {"to_email": to_email} if to_email else {}
    resp = await mcp.call_tool("process_f1_to_sheet_and_email", args)
    content = getattr(resp, "content", None)
    if hasattr(content, "text"):
        print(content.text)
    else:
        print(str(resp))


if __name__ == "__main__":
    asyncio.run(main())

