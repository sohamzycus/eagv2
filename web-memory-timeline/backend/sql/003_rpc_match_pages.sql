-- RPC: match_pages
-- Usage: select * from match_pages(<vector>, 0.2, 10)

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

-- Optional: filter similarity >= match_threshold on the client side.
