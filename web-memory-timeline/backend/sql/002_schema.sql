-- Schema for sessions and pages with pgvector

create table if not exists public.sessions (
  id uuid primary key default gen_random_uuid(),
  start_ts bigint not null,
  end_ts bigint not null,
  title text,
  created_at timestamp with time zone default now()
);

create table if not exists public.pages (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references public.sessions(id) on delete cascade,
  url text not null,
  title text,
  snippet text,
  ts bigint not null,
  embedding vector(768),
  created_at timestamp with time zone default now()
);

-- Indexes
create index if not exists pages_session_id_idx on public.pages(session_id);
create index if not exists pages_url_idx on public.pages using gin (to_tsvector('simple', coalesce(url,'') || ' ' || coalesce(title,'') || ' ' || coalesce(snippet,'')));

-- Vector index (requires pgvector 0.5+)
create index if not exists pages_embedding_ivfflat on public.pages using ivfflat (embedding vector_cosine_ops) with (lists = 100);
