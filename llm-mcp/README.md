llm-mcp — Agent + MCP Tools (Gmail, GDrive/Sheets, Web, Inbox SSE)

Overview
- This project runs a reasoning agent that discovers and calls MCP tools. It supports:
  - Gmail (send email)
  - Google Sheets/Drive (create sheet, append rows, share)
  - Web search/fetch
  - Local Inbox (SSE) to receive tasks on localhost without external chat apps
  - A “workflows” server with a fast end-to-end pipeline for F1 standings → Sheet → Email

Key Components
- Agent
  - `agent.py`: entry point; runs `AgentLoop`
  - `core/loop.py`: main loop, including fast-path routing and a deterministic F1 pipeline
  - `core/session.py`: MultiMCP dispatcher; discovers tools from configured servers; supports stdio + SSE
  - `core/strategy.py`: planning wrapper; enforces guardrails (e.g., don’t accept premature FINAL_ANSWER)
  - `modules/*`: perception, decision, parser, memory, model manager
- MCP Servers
  - `mcp_server_inbox.py` (SSE): HTTP POST /enqueue tasks; tools: `fetch_task`, `peek_tasks`, `clear_tasks`
  - `mcp_server_workflows.py` (stdio): tools: `get_f1_standings`, `process_f1_to_sheet_and_email`
  - `mcp_server_gdrive.py` (stdio): tools: `create_spreadsheet`, `append_values`, `share_file`
  - `mcp_server_gmail.py` (stdio): tool: `send_email`
  - `mcp_server_1.py` (stdio): math/utilities
  - `mcp_server_2.py` (stdio): RAG + extraction
  - `mcp_server_3.py` (stdio): DuckDuckGo search + generic content fetch
- Configuration
  - `config/profiles.yaml`: agent profile, strategy, memory, and list of MCP servers (stdio/SSE)
  - `ENV.example`: example .env for local development
  - `RUN.md`: quick run guide

Architecture (high-level)
- User input → AgentLoop
  1) Fast-path check (inbox fetch, or direct workflow match such as F1)
  2) If no fast-path → Perception (intent/tools hint) → Strategy → Plan
  3) Plan produces a single-line FUNCTION_CALL or FINAL_ANSWER
  4) Tool execution via MultiMCP (maps tool to its server and transport)
  5) Results are added to memory; agent iterates or ends with FINAL_ANSWER
- Inbox SSE
  - POST `http://127.0.0.1:8780/enqueue` to queue tasks
  - Agent can `fetch_task` from SSE server at `http://127.0.0.1:8000/sse`
- F1 Workflow (fast path)
  - Calls MCP tools deterministically: `get_f1_standings` → `create_spreadsheet` → `append_values` → `share_file` → `send_email`
  - Returns a JSON summary with `sheetUrl`, `sheetId`, and `emailStatus`

Environment Variables
- Create `llm-mcp/.env` from `ENV.example` and set:
  - GOOGLE_CREDENTIALS_PATH=./secrets/credentials.json
  - GOOGLE_TOKEN_PATH=./secrets/token.json
  - GMAIL_DEFAULT_TO=you@example.com
  - INSECURE_SSL=0 (set to 1 in strict corporate TLS environments)
  - Optional (only if using Gemini): GEMINI_API_KEY

Google OAuth (one-time)
- Generate `token.json` with required scopes (Sheets, Drive, Gmail Send). Example:
  - Scopes:
    - https://www.googleapis.com/auth/spreadsheets
    - https://www.googleapis.com/auth/drive
    - https://www.googleapis.com/auth/gmail.send
  - Use the helper snippet from RUN.md or your own local app flow to write `token.json`

Install
- From repo root:
  - uv pip install -e ./llm-mcp

Start Local Inbox (SSE)
- Terminal A:
```bash
uv run python llm-mcp/mcp_server_inbox.py
```
- Enqueue a task (new terminal):
```bash
curl -X POST http://127.0.0.1:8780/enqueue \
  -H "Content-Type: application/json" \
  -d '{"task":"Find the current F1 driver standings, put them into a Google Sheet, and email me the link."}'
```

Run the Agent
- Terminal B:
```bash
cd llm-mcp
printf "Fetch the next inbox task and execute it end-to-end." | uv run python agent.py
```
- The agent will:
  - Discover tools from all configured servers
  - Fetch the task from the inbox
  - Recognize the F1 workflow and execute it (fast path)
  - Print a final JSON with the Google Sheet link and email status

Direct Workflow Test (no agent)
- Useful for quick verification:
```bash
uv run python llm-mcp/run_workflow.py
```
- Expected: JSON containing `sheetUrl`, `sheetId`, and email status

Corporate TLS/Proxy
- If HTTPS requests (Ergast/Wikipedia/F1/ESPN or Google APIs) fail with certificate errors:
  - Set `INSECURE_SSL=1` in `llm-mcp/.env` (tools respect this toggle)
  - Preferred: set a corporate CA instead of disabling verification:
    - REQUESTS_CA_BUNDLE=path\to\corp-ca.pem
    - SSL_CERT_FILE=path\to\corp-ca.pem
    - HTTPLIB2_CA_CERTS=path\to\corp-ca.pem

Notes
- The “math/documents/websearch” servers aren’t required for the F1→Sheet→Email demo, but they’re kept as examples and for future extensions.
- The agent avoids long stalls by:
  - Skipping memory embedding on a cold start
  - Timeouts around server init/tool listing
  - Deterministic fast-paths for common workflows (like F1)


