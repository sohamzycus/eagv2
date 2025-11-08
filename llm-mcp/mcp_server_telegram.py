import os
import sys
import asyncio
from typing import Optional, List
import requests
from mcp.server.fastmcp import FastMCP, Context


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DEFAULT_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

mcp = FastMCP("telegram-bot")


def _require_token() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN in environment")


@mcp.tool()
async def send_message(text: str, ctx: Context, chat_id: Optional[str] = None) -> str:
    """
    Send a Telegram message.
    Usage: send_message|text="hello world"
    Optional: chat_id (defaults to TELEGRAM_CHAT_ID)
    """
    _require_token()
    cid = chat_id or DEFAULT_CHAT_ID
    if not cid:
        return "ERROR: chat_id is required (set TELEGRAM_CHAT_ID or pass chat_id)"

    try:
        resp = requests.post(f"{API_BASE}/sendMessage", json={"chat_id": cid, "text": text})
        resp.raise_for_status()
        await ctx.info("Message sent")
        return "OK"
    except Exception as e:
        await ctx.error(f"Failed to send message: {e}")
        return f"ERROR: {e}"


@mcp.tool()
async def get_updates(offset: Optional[int] = None, ctx: Context = None, timeout_sec: int = 0) -> list[str]:
    """
    Poll Telegram updates (long-poll optional via timeout_sec).
    Returns list of 'chat_id: text' strings.
    """
    _require_token()
    params = {"timeout": timeout_sec}
    if offset is not None:
        params["offset"] = offset
    try:
        resp = requests.get(f"{API_BASE}/getUpdates", params=params, timeout=timeout_sec + 10)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for upd in data.get("result", []):
            msg = upd.get("message") or {}
            chat = msg.get("chat", {})
            text = msg.get("text", "")
            cid = chat.get("id")
            if cid and text:
                results.append(f"{cid}: {text}")
        if ctx:
            await ctx.info(f"Fetched {len(results)} updates")
        return results
    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to get updates: {e}")
        return [f"ERROR: {e}"]


@mcp.tool()
async def get_me(ctx: Context) -> str:
    """Return basic bot info."""
    _require_token()
    try:
        resp = requests.get(f"{API_BASE}/getMe")
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        await ctx.error(f"Failed to getMe: {e}")
        return f"ERROR: {e}"


if __name__ == "__main__":
    host = os.getenv("MCP_SSE_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_SSE_PORT", "8765"))
    path = os.getenv("MCP_SSE_PATH", "/sse")
    print(f"telegram SSE server starting at http://{host}:{port}{path}")
    # Run HTTP SSE transport
    mcp.run(transport="sse", host=host, port=port, path=path)

