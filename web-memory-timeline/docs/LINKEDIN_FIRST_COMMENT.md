# First Comment (copy‑paste)

Architecture at a glance
- Extension (MV3) → exports visits.json (sessions grouped by 15‑min idle gap)
- Ingest → Ollama embeddings (nomic‑embed‑text, 768‑dim) → Supabase (pgvector)
- Search → Next.js API embeds query → RPC does cosine+threshold → UI shows timeline + snippet highlight
- Optional offline path → FAISS (IndexFlatIP + normalized vectors)

Mini diagram
[Extension] → visits.json → [Embeddings (Ollama)] → [pgvector in Supabase]
                                   ↘︎ (optional) FAISS files
Frontend (Next.js) → /api/embed-text → Ollama → RPC match_pages → Results

Key choices
- Local‑first stack (Ollama + Supabase + Next.js)
- 768‑dim embeddings for better recall
- Threshold‑aware search so weak matches don’t flood results
- Text Fragments (#:~:text=) to jump to the matched snippet on the original page

Tiny code bites (kept short)
RPC: threshold‑aware cosine on vector(768)
```sql
create or replace function public.match_pages(
  query_embedding vector(768), match_threshold float, match_count int
) returns table(id uuid, url text, title text, snippet text, similarity float, session_id uuid)
language sql stable as $$
  select p.id, p.url, p.title, p.snippet,
         1 - (p.embedding <=> query_embedding) as similarity,
         p.session_id
  from public.pages p
  where 1 - (p.embedding <=> query_embedding) >= match_threshold
  order by p.embedding <=> query_embedding asc
  limit match_count;
$$;
```
Next.js API → Ollama embeddings (query side)
```ts
export async function POST(req: Request) {
  const { text } = await req.json();
  const r = await fetch(`${process.env.OLLAMA_BASE_URL}/api/embeddings`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: process.env.OLLAMA_EMBED_MODEL || 'nomic-embed-text',
                           prompt: String(text).slice(0,4000) })
  });
  return new Response(JSON.stringify({ embedding: (await r.json()).embedding }),
                      { headers: { 'Content-Type': 'application/json' } });
}
```

Try it locally
- Generate: `node tools/generate_large_samples.mjs visits_large.json`
- Ingest: `node tools/ingest_visits_to_supabase.mjs visits_large.json`
- (Optional) FAISS: `python tools/build_faiss_local.py visits_large.json --out faiss_out`
- Run: `npm run dev -- -p 3005` → search “pgvector”, “faiss”, “next.js”

Links
- Demo: https://youtu.be/7qOuFtY_vKU
- Code: https://github.com/sohamzycus/eagv2/tree/master/web-memory-timeline
