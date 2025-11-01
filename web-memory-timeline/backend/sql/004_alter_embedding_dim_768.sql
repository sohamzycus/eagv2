-- Alter embedding dimension to 768 for nomic-embed-text compatibility
-- 1) Drop vector index (depends on dimension)
drop index if exists pages_embedding_ivfflat;

-- 2) Alter column dimension
alter table public.pages alter column embedding type vector(768);

-- 3) Recreate vector index
create index if not exists pages_embedding_ivfflat on public.pages using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- 4) Recreate RPC with 768-dim signature
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
  order by p.embedding <=> query_embedding asc
  limit match_count;
$$;
