# Social Templates

## LinkedIn (long-form)
🚀 Shipped a personal "Web Memory & Context Timeline" — a privacy‑first way to remember the web.

What it does:
- Captures browsing sessions (optional Chrome extension)
- Builds semantic embeddings (Ollama, nomic‑embed‑text)
- Stores vectors in Supabase (pgvector)
- Next.js app lets me search + replay timelines with text‑fragment highlighting

Why it matters:
- I can instantly find articles I skimmed last week
- All captured locally; I choose what to export
- Fully free/open stack; runs on a laptop

Under the hood:
- Extension (MV3) → `visits.json`
- Ingest → Ollama embeddings (768‑dim) → Supabase
- RPC vector search → Next.js UI

Demo clip in comments 👇 (local run + search)

Repo: <your repo link>
#nextjs #supabase #ollama #pgvector #ai #productivity #opensource

## LinkedIn (short)
Built a privacy‑first "Web Memory" that turns my browsing into a searchable timeline.
Ollama + Supabase + Next.js. Demo below 👇

## X / Threads
I forget web pages. Now I don’t. Extension → embeddings → vector search in a Next.js app.
Open stack: Ollama + Supabase. Demo👇 #nextjs #supabase #ollama
