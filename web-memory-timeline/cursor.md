# Cursor Prompt — Web Memory & Context Timeline App (Extension + App)

Use this file with Cursor to generate and maintain the project. It mirrors the design you provided.

## Project Goal (one-liner)

Build a Personal Web Memory system that records your browsing sessions (optional extension), indexes content semantically, and lets you search and replay timelines — deployed to free services and working first-time-right.

## Deliverables
- `extension/` — MV3 Chrome extension
- `colab/` — `index_builder.ipynb` to build embeddings + FAISS
- `backend/` — Supabase SQL migrations + RPC + example Edge Function
- `frontend/` — Next.js 15 app with search/timeline/highlighting
- `docs/` — setup & troubleshooting docs
- `README.md` at repo root

## Notes
- Privacy-first, no background scraping of confidential sites (blacklist Gmail/WhatsApp/banks)
- Two flows: Full auto (extension) or App-only (upload history/paste URLs)
- Use text fragments for highlighting: `#:~:text=`

Refer to the repo structure and docs for full instructions.
