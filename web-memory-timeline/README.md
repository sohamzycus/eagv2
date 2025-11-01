# Web Memory & Context Timeline

Personal web memory system: capture browsing sessions (optional Chrome extension), index content with embeddings (Colab or Supabase), and search/replay timelines in a Next.js frontend.

## Quick Start

1. Chrome Extension
   - See `extension/README.md`
   - Load unpacked, browse, export `visits.json`

2. Build Index (Colab)
   - Open `colab/index_builder.ipynb`
   - Upload `visits.json`
   - Download `index.faiss`, `vectors.npy`, `metadata.json`

3. Backend (Supabase)
   - Run SQL in `backend/sql/`
   - Configure Storage bucket and RPC

4. Frontend
   - Copy `.env.example` to `.env.local`
   - `cd frontend && npm i && npm run dev`

## Deploy
- Frontend: Vercel (set `NEXT_PUBLIC_*` env vars)
- Backend: Supabase (SQL + optional Edge Functions)

## Privacy
- Extension stores locally; export only on demand
- Default blacklist for private domains
