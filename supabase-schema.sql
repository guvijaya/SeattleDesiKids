-- KidsBook Supabase Schema
-- Run this in the Supabase SQL editor: https://app.supabase.com → SQL Editor

-- ─────────────────────────────────────────────
-- 1. Tables
-- ─────────────────────────────────────────────

-- Reading progress: one row per user per essay
create table if not exists reading_progress (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid references auth.users(id) on delete cascade,
  slug       text not null,
  lang       text not null,
  rating     smallint check (rating between 1 and 5),
  read_at    timestamptz default now(),
  unique(user_id, slug)
);

-- Comments: require admin approval before becoming visible
create table if not exists essay_comments (
  id           uuid primary key default gen_random_uuid(),
  slug         text not null,
  user_id      uuid references auth.users(id) on delete cascade,
  display_name text,
  body         text not null,
  approved     boolean default false,
  created_at   timestamptz default now()
);

-- ─────────────────────────────────────────────
-- 2. Row Level Security
-- ─────────────────────────────────────────────

alter table reading_progress enable row level security;
alter table essay_comments enable row level security;

-- reading_progress: users can read/write only their own rows
create policy "Users read own progress"
  on reading_progress for select
  using (auth.uid() = user_id);

create policy "Users insert own progress"
  on reading_progress for insert
  with check (auth.uid() = user_id);

create policy "Users update own progress"
  on reading_progress for update
  using (auth.uid() = user_id);

-- essay_comments: public reads approved rows; auth users insert; users delete own
create policy "Public reads approved comments"
  on essay_comments for select
  using (approved = true);

create policy "Auth users insert comments"
  on essay_comments for insert
  with check (auth.uid() = user_id);

create policy "Users delete own comments"
  on essay_comments for delete
  using (auth.uid() = user_id);

-- Admin (any authenticated user with admin role) can update approved flag
-- We rely on your admin page checking the user ID client-side;
-- for extra security you can add a policy using a custom claim or a separate admin table.
create policy "Anyone authenticated can update approval"
  on essay_comments for update
  using (auth.uid() is not null);

-- ─────────────────────────────────────────────
-- 3. Indexes
-- ─────────────────────────────────────────────

create index if not exists idx_reading_progress_user on reading_progress(user_id);
create index if not exists idx_essay_comments_slug on essay_comments(slug, approved);
