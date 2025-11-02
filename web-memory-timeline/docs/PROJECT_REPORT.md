# Project Report – Web Memory & Context Timeline

## Goal
Personal Web Memory system that captures browsing sessions (Chrome extension), indexes semantically (Ollama embeddings + Supabase pgvector), and lets users search and replay timelines (Next.js UI). Deployed to Vercel, free stack compatible.

## Architecture
- Extension (MV3): captures `url,title,snippet,ts`, groups into sessions (15‑min idle gap), exports `visits.json`.
- Indexing:
  - Option A: Local ingest using Ollama (nomic-embed-text, 768‑dim) → Supabase `pages.embedding vector(768)`
  - Option B: Colab (FAISS artifacts) for offline search
- Backend (Supabase): Postgres tables `sessions`, `pages` + RPC `match_pages(query_embedding vector(768), ...)` with cosine similarity
- Frontend (Next.js 15, App Router): UI for Search, Upload, Timeline; `/api/embed-text` calls local Ollama; result links use Text Fragments (`#:~:text=`)

## Key Files
- `extension/`: `manifest.json`, `content_script.js`, `background.js`, `sessionManager.js`, `popup.*`
- `backend/sql/`: `001_extensions.sql`, `002_schema.sql`, `003_rpc_match_pages.sql`, `004_alter_embedding_dim_768.sql`
- `tools/`: `mock_extension_export.js`, `ingest_visits_to_supabase.mjs`
- `frontend/`: Next.js app, Tailwind, Supabase client, embed API
- `docs/`: setup, demo, troubleshooting

## Notable Decisions
- Privacy-first: no auto‑uploads; export by user
- 768‑dim embeddings (nomic-embed-text) → aligned schema and RPC
- Local embeddings for dev; production can either tunnel Ollama or precompute

## What We Implemented
- End-to-end ingestion and semantic search using Supabase RPC
- Robust local demo and video‑ready steps (see `docs/LOCAL_DEMO.md`)
- Vercel-ready build config and environment

## Next
- Timeline replay UI polish (framer‑motion)
- Client-side fallback search with precomputed embeddings.json for offline use
- Advanced highlight selection (sentence boundaries + scoring)
