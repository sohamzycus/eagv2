# Demo Video Script & Shot List

Duration: 60–90 seconds (fast cut), ~3–4 minutes (detailed)

## Hook (5 sec)
- On camera (or VO + screen): “I built a privacy‑first Web Memory that turns your browsing into a searchable timeline.”

## Step 1 – Prepare visits.json (10–20 sec)
- Terminal: `node tools/generate_large_samples.mjs visits_large.json`
- Show the file opens briefly in editor.

## Step 2 – Build FAISS index (10–20 sec)
- Terminal: `python tools/build_faiss_local.py visits_large.json --out faiss_out`
- Finder/Explorer: show `faiss_out/index.faiss`, `vectors.npy`, `metadata.json`.
- Optional: quick CLI search: `python tools/search_faiss_local.py --query "vector search"`

## Step 3 – Ingest to Supabase (10–15 sec)
- Terminal: `node tools/ingest_visits_to_supabase.mjs visits_large.json`
- Show logs: `Inserted session`, `+ page ...`
- Supabase UI: show `pages` rows exist.

## Step 4 – App search (20–30 sec)
- Start app: `npm run dev -- -p 3005`
- Browser: http://127.0.0.1:3005
- Query: `next.js`, `pgvector`, `ollama`
- Click a result → real page opens with text fragment highlight.

## Close (5 sec)
- “Open stack: Ollama + Supabase + Next.js. Code & steps in the repo. Link below.”

## Recording Tips
- Windows: use Xbox Game Bar (Win+G) or OBS.
- Capture 1080p @ 60fps; keep terminal font large.
- Keep commands copy‑pasted from `docs/LOCAL_DEMO.md`.
- Trim dead time; keep cuts brisk.
