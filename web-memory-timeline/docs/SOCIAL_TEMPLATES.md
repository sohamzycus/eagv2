# Social Templates

## LinkedIn (concise – ready to paste)
I wanted a way to actually remember the web — not just tabs. So I built a privacy‑first Web Memory & Context Timeline.

Demo video: https://youtu.be/7qOuFtY_vKU  
Code: https://github.com/sohamzycus/eagv2/tree/master/web-memory-timeline

What it does
- Captures browsing sessions (MV3 extension, export on demand)
- Indexes semantically with Ollama embeddings (nomic‑embed‑text, 768‑dim)
- Stores vectors in Supabase (pgvector)
- Optional FAISS index for fast local/offline search
- Next.js app: search + timeline replay; results open the original page with a text‑fragment highlight

How it works (super short)
- Session grouping: new session after 15‑min idle gap
- Embeddings: Next.js API → Ollama (query + documents)
- Vector search: cosine over `vector(768)` with a threshold to filter weak matches
- Optional offline: FAISS (IndexFlatIP + normalized vectors)

Why it matters
- Find that “I saw it last week” page in seconds
- Local by default; you choose what to export
- Free/open stack that runs on a laptop

Try it
- Clone the repo and run docs/LOCAL_DEMO.md
- Search for “pgvector”, “faiss”, “next.js” — then jump straight to the matched snippet

#nextjs #supabase #pgvector #ollama #faiss #webdev #productivity #opensource

---

## LinkedIn (short)
Built a privacy‑first Web Memory that turns browsing into a searchable timeline.  
Demo: https://youtu.be/7qOuFtY_vKU  ·  Code: https://github.com/sohamzycus/eagv2/tree/master/web-memory-timeline  
Ollama + Supabase + Next.js (+ FAISS offline).

---

## First comment suggestion (to boost engagement)
- Tech stack: Next.js (App Router), Ollama `nomic‑embed‑text` (768‑dim), Supabase/pgvector (`1 − (embedding <=> query)`), FAISS IndexFlatIP.
- Data flow: extension → visits.json → embeddings → pgvector RPC with threshold → UI search + text‑fragment highlight.
- Repo has a one‑command local demo and a short video script.
