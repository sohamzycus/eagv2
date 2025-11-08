# llm-mcp Codebase Overview

## High-Level Flow
- `agent.py` starts the interactive CLI, asks for the user goal, loads profiles from `config/profiles.yaml`, constructs a `MultiMCP`, and runs the agent loop.
- `MultiMCP` (in `core/session.py`) discovers tools from each configured MCP stdio server and keeps a map so each tool call can reconnect to the correct script on demand.
- `AgentLoop` (in `core/loop.py`) coordinates perception → memory retrieval → planning → tool execution until it sees `FINAL_ANSWER` or the max step count.

## Core Components
- **Context & Profile:** `AgentContext` (`core/context.py`) loads agent persona, memory settings, and strategy. It tracks session metadata, step count, tool traces, and the embedded memory store.
- **Perception:** `modules/perception.py` prompts an LLM (via `ModelManager`) to extract intent/entities/tool hints from raw user input for downstream planners.
- **Planning:** `modules/decision.py` generates a single-line `FUNCTION_CALL` or `FINAL_ANSWER`, while `core/strategy.py` wraps it with hint-based tool filtering and strategy rules.
- **Memory:** `modules/memory.py` manages FAISS-backed semantic memory, posting to the configured embedding endpoint and retrieving prior tool outputs relevant to the current query.
- **Model Management:** `modules/model_manager.py` reads `config/models.json` and the active profile to choose between Gemini or local Ollama-style endpoints for text generation and embeddings.

## MCP Servers
- `mcp_server_1.py` – Math & utility toolbox (arithmetic, trig, factorial, Fibonacci, sandboxed Python, shell, SQL, thumbnail generation, greeting resource). Exposed via FastMCP.
- `mcp_server_2.py` – Local RAG pipeline (document ingestion, semantic chunking, image captioning, FAISS indexing). Provides tools like `search_documents`, `extract_pdf`, and `extract_webpage`.
- `mcp_server_3.py` – Live DuckDuckGo search & content fetcher with rate limiting, BeautifulSoup parsing, and formatted results.

## Configuration & Assets
- `config/profiles.yaml` defines agent identity, strategy, memory defaults, LLM selection, and the list of MCP servers (scripts + working directories).
- `config/models.json` enumerates supported generation/embedding backends alongside API keys or local endpoints.
- `documents/` stores source files (PDFs, markdown, etc.) that feed the RAG index; `faiss_index/` caches the built index and metadata.


