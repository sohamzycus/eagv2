-- RPC: match_pages (threshold-aware, 768-dim)
-- Usage example:
--   select * from match_pages(
--     (select embedding from public.pages where title = 'FAISS' limit 1),
--     0.55,
--     10
--   );

create or replace function public.match_pages(
  query_embedding vector(768),
  match_threshold float,
  match_count int
)
returns table(
  id uuid,
  url text,
  title text,
  snippet text,
  similarity float,
  session_id uuid
)
language sql stable as
$$
  select p.id, p.url, p.title, p.snippet,
         1 - (p.embedding <=> query_embedding) as similarity,
         p.session_id
  from public.pages p
  where p.embedding is not null
    and 1 - (p.embedding <=> query_embedding) >= match_threshold
  order by p.embedding <=> query_embedding asc
  limit match_count;
$$;
