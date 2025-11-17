import os
import json
import threading
import asyncio
from typing import Optional, List
from collections import deque

from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv

load_dotenv()

# Simple in-memory queue with thread-safe access
_queue: deque[str] = deque()
_lock = asyncio.Lock()

mcp = FastMCP("local-inbox")


@mcp.tool()
async def fetch_task(ctx: Context) -> str:
    """
    Fetch and remove the next task from the inbox queue.
    Returns 'NONE' if queue is empty.
    """
    async with _lock:
        if not _queue:
            return "NONE"
        task = _queue.popleft()
        await ctx.info("Fetched one task from inbox")
        return task


@mcp.tool()
async def peek_tasks(limit: int = 10, ctx: Context = None) -> list[str]:
    """
    Peek at up to 'limit' tasks without removing them.
    """
    async with _lock:
        items = list(_queue)[:max(0, limit)]
    if ctx:
        await ctx.info(f"Peeked {len(items)} tasks")
    return items


@mcp.tool()
async def clear_tasks(ctx: Context) -> str:
    """
    Clear all tasks from the inbox.
    """
    async with _lock:
        _queue.clear()
    await ctx.info("Cleared inbox")
    return "OK"


# Minimal local HTTP API for enqueueing tasks
def start_http_api(host: str, port: int, path: str):
    # A tiny Starlette app just for POST /enqueue
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse, PlainTextResponse
    from starlette.requests import Request
    from starlette.routing import Route
    import uvicorn

    async def health(_: Request):
        return PlainTextResponse("OK")

    async def enqueue(request: Request):
        try:
            data = await request.json()
        except Exception:
            return JSONResponse({"error": "invalid JSON"}, status_code=400)
        task = data.get("task")
        if not task or not isinstance(task, str):
            return JSONResponse({"error": "task (string) required"}, status_code=400)
        async with _lock:
            _queue.append(task)
        return JSONResponse({"status": "enqueued", "size": len(_queue)})

    routes = [
        Route("/health", health, methods=["GET"]),
        Route("/enqueue", enqueue, methods=["POST"]),
    ]

    app = Starlette(routes=routes)

    # Run uvicorn in a background thread
    def run_server():
        uvicorn.run(app, host=host, port=port, log_level="info")

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()


if __name__ == "__main__":
    # Start local HTTP enqueue API
    INBOX_HTTP_HOST = os.getenv("INBOX_HTTP_HOST", "127.0.0.1")
    INBOX_HTTP_PORT = int(os.getenv("INBOX_HTTP_PORT", "8780"))
    start_http_api(INBOX_HTTP_HOST, INBOX_HTTP_PORT, "/")

    # Start MCP over SSE
    print(f"Local inbox HTTP API:  http://{INBOX_HTTP_HOST}:{INBOX_HTTP_PORT}/enqueue")
    print("Local inbox MCP (SSE): http://127.0.0.1:8000/sse")
    # Default SSE runner (binds to 0.0.0.0:8000, path /sse)
    mcp.run(transport="sse")

