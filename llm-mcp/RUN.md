Setup and Run Guide

1) Install deps
- Ensure Python >= 3.11
- From repo root:
  - uv pip install -e ./llm-mcp  (or) pip install -e ./llm-mcp

2) Prepare environment
- Copy `llm-mcp/ENV.example` to `llm-mcp/.env` and fill:
  - TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
  - GOOGLE_TOKEN_PATH, GOOGLE_CREDENTIALS_PATH
  - Optional: GEMINI_API_KEY
- Place your Google OAuth files:
  - credentials.json (client secrets) and token.json (authorized) under the paths you set.

3) Start servers
- Telegram SSE server:
  - cd llm-mcp
  - set -a && . ./.env && set +a   (or export variables on Windows/PowerShell)
  - python mcp_server_telegram.py
  - It starts at http://127.0.0.1:8765/sse by default.
- Document RAG, Math, Websearch servers (stdio):
  - These are started on-demand by the agent via stdio.
- Gmail and GDrive servers (stdio):
  - Also started on-demand by the agent via stdio.

4) Configure profile
- `llm-mcp/config/profiles.yaml` already contains entries:
  - gmail (stdio), gdrive (stdio), telegram (SSE url http://127.0.0.1:8765/sse)

5) Run the agent
- cd llm-mcp
- python agent.py
- Example Telegram-driven task to try:
  "Find the current F1 driver standings, put them into a Google Sheet, share the sheet link to me via Gmail, and confirm on Telegram."

Notes
- Google APIs require you to run the OAuth flow locally once to generate token.json.
- Keep secrets out of git. Use `ENV.example` as a guide.

