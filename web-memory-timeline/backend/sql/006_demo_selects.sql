-- DEMO SQLS: run these in Supabase SQL editor

-- 1) Quick sanity: counts
select (select count(*) from public.sessions) as sessions,
       (select count(*) from public.pages)    as pages;

-- 2) Peek a few pages
select id, title, url, left(snippet, 80) as snippet
from public.pages
limit 10;

-- 3) Self-similarity example using a page as the query vector
--    (Pick a known title present in your dataset)
select p2.id, p2.title, p2.url,
       1 - (p2.embedding <=> q.embedding) as similarity
from (select embedding from public.pages where title = 'FAISS' limit 1) as q,
     public.pages p2
order by p2.embedding <=> q.embedding asc
limit 10;

-- 4) Call the RPC with a real embedding and a threshold
select *
from public.match_pages(
  (select embedding from public.pages where title = 'FAISS' limit 1),
  0.55,   -- threshold (tune 0.4..0.7)
  10      -- top-k
);

-- 5) Try another seed (e.g., Next.js)
select *
from public.match_pages(
  (select embedding from public.pages where title ~* 'next' limit 1),
  0.55,
  10
);
