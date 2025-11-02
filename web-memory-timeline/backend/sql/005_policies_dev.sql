-- DEV RLS POLICIES (safe defaults for local testing)
-- NOTE: Service role bypasses RLS, but these policies allow anon/auth inserts in dev.

-- Enable RLS
alter table public.sessions enable row level security;
alter table public.pages    enable row level security;

-- Sessions: read for everyone
drop policy if exists "public read sessions" on public.sessions;
create policy "public read sessions"
  on public.sessions
  for select
  using (true);

-- Sessions: insert for everyone (DEV ONLY)
drop policy if exists "ingest insert sessions" on public.sessions;
create policy "ingest insert sessions"
  on public.sessions
  for insert
  with check (true);

-- Pages: read for everyone
drop policy if exists "public read pages" on public.pages;
create policy "public read pages"
  on public.pages
  for select
  using (true);

-- Pages: insert for everyone (DEV ONLY)
drop policy if exists "ingest insert pages" on public.pages;
create policy "ingest insert pages"
  on public.pages
  for insert
  with check (true);
