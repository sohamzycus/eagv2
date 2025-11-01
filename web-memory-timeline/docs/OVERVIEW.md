# Overview

This project captures browsing sessions, builds semantic indexes (FAISS or pgvector), and lets you search/replay a timeline via a Next.js frontend.

## Flow

- Capture: Chrome extension groups visits into sessions and exports `visits.json`.
- Indexing: Colab notebook (or Supabase Edge Function) generates embeddings and FAISS artifacts.
- Storage: Upload artifacts to Supabase Storage or store vectors in Postgres (pgvector).
- Frontend: Next.js app queries vectors and shows a timeline with text fragment highlighting.

## Privacy
- Local-only capture; export is user-initiated.
- Default blacklist for private domains.
