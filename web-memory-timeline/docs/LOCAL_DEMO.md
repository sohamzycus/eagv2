# Local Demo – Web Memory & Context Timeline

This guide runs the complete flow on your laptop, ready for a video capture.

## Prerequisites
- Node.js 20.x + npm 10
- Ollama running locally: `ollama serve`
- Supabase project with tables and RPC created
  - Run SQL files in `backend/sql/` (or the alter script `004_alter_embedding_dim_768.sql`)

## 0) Clone and install (first time)
```bash
cd C:/Codebase/personal/eagv2/web-memory-timeline/frontend
npm ci --no-audit --no-fund
```

## 1) Start Ollama and pull embed model
```bash
ollama serve
ollama pull nomic-embed-text
```

## 2) Generate sample visits.json (or export from extension)
```bash
cd C:/Codebase/personal/eagv2/web-memory-timeline
node tools/mock_extension_export.js visits.json
```

## 3) Ingest into Supabase (server-side)
Set these envs in PowerShell (replace with your values):
```powershell
$env:SUPABASE_URL = "https://<project>.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY = "<service_role_key>"
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:OLLAMA_EMBED_MODEL = "nomic-embed-text"
node tools/ingest_visits_to_supabase.mjs visits.json
```
This inserts `sessions` and `pages` and stores 768‑dim embeddings.

## 4) Configure frontend env
Create/edit `frontend/.env.local`:
```
NEXT_PUBLIC_SUPABASE_URL=https://<project>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon_key>
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text
```

## 5) Run the app
```bash
cd C:/Codebase/personal/eagv2/web-memory-timeline/frontend
npm run dev -- -p 3005
```
Open http://127.0.0.1:3005 and search terms like:
- `example`, `example domain`
- `next.js`, `supabase docs`
- `pgvector`, `faiss`, `ollama embed`

## 6) Video capture checklist
- Show `visits.json` generation
- Show ingest logs (`+ page ...`)
- Show app: search → results → link opens with text fragment highlight
- Optional: expand `samples/visits.sample.json`, regenerate, re‑ingest, and search again

## Troubleshooting
- Embeddings length must be 768. If you see a vector dimension error, run `004_alter_embedding_dim_768.sql` in Supabase.
- If RPC returns empty: re‑run `003_rpc_match_pages.sql` (vector(768)) and confirm RLS read policy on `pages`.
- If `/api/embed-text` fails: ensure `ollama serve` and model `nomic-embed-text` are available.

## 2b) Build FAISS locally (optional, for demo clip)
This shows indexing to a FAISS file and uploading artifacts to Supabase Storage.

```bash
cd C:/Codebase/personal/eagv2/web-memory-timeline
python -m venv .venv && .venv/Scripts/activate
pip install -r tools/requirements_faiss.txt
# build from visits.json → faiss_out/{index.faiss,vectors.npy,metadata.json}
python tools/build_faiss_local.py visits.json --out faiss_out
# optional upload to Supabase Storage (set envs first)
$env:SUPABASE_URL="https://<project>.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY="<service_role_key>"
python tools/build_faiss_local.py visits.json --out faiss_out
```
Record a quick pan over `faiss_out/` and (if uploaded) the Supabase Storage bucket.

## 2c) Query FAISS with CLI (offline search demo)
```bash
# After building faiss_out/
python tools/search_faiss_local.py --index faiss_out/index.faiss --vectors faiss_out/vectors.npy --meta faiss_out/metadata.json --k 5 --query "vector search in postgres"
```
This prints the top matches with cosine similarity, proving the FAISS artifacts work independently of the app.
