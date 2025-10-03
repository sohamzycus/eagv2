# MSPaint MCP - Production-ready (v2)

This version adds:
- Gemini 2.0 Flash integration (Google GenAI) with optional OpenAI-compatible fallback.
- DPI detection and scaling using Windows APIs with fallbacks.
- Improved Paint/Text-tool selection supporting Paint 3D and classic Paint using UIA element search.
- Full request/response logging for LLM calls (raw model request and raw response saved).

## Setup
- Windows desktop is required to run automation.
- Install required packages:
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```
- If you want to use Gemini via Google GenAI, also install `google-genai`:
  ```powershell
  pip install google-genai
  ```
- Alternatively, you can use OpenAI-compatible client if your environment supports it; set env var `OPENAI_API_KEY`.

## Authentication
- For Google Gemini (preferred): set environment variable `GOOGLE_API_KEY` with your Gemini API key.
- For OpenAI-compatible mode (alternative): set `OPENAI_API_KEY`.

## Run demo
  ```powershell
  python run_demo.py
  ```

## Captured logs
- LLM raw request and raw response are saved into the session JSON produced by the agent (field `llm_raw_request` and `llm_raw_response`).
