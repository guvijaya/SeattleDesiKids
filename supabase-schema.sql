-- KidsBook Supabase data schema for Firebase Authentication.
-- For an existing database, apply supabase-firebase-migration.sql instead.

-- Reading progress: one row per Firebase user per essay.
create table if not exists reading_progress (
  id         uuid primary key default gen_random_uuid(),
  user_id    text,
  slug       text not null,
  lang       text not null,
  rating     smallint check (rating between 1 and 5),
  read_at    timestamptz default now(),
  unique(user_id, slug)
);

-- Comments are private until a Firebase admin approves them.
create table if not exists essay_comments (
  id           uuid primary key default gen_random_uuid(),
  slug         text not null,
  user_id      text,
  display_name text,
  body         text not null,
  approved     boolean default false,
  created_at   timestamptz default now()
);

alter table reading_progress enable row level security;
alter table essay_comments enable row level security;

drop policy if exists "Users read own progress" on reading_progress;
drop policy if exists "Users insert own progress" on reading_progress;
drop policy if exists "Users update own progress" on reading_progress;
drop policy if exists "Firebase users read own progress" on reading_progress;
drop policy if exists "Firebase users insert own progress" on reading_progress;
drop policy if exists "Firebase users update own progress" on reading_progress;

create policy "Firebase users read own progress"
  on reading_progress for select
  using (
    (auth.jwt() ->> 'role') = 'authenticated'
    and user_id = (auth.jwt() ->> 'sub')
  );

create policy "Firebase users insert own progress"
  on reading_progress for insert
  with check (
    (auth.jwt() ->> 'role') = 'authenticated'
    and user_id = (auth.jwt() ->> 'sub')
  );

create policy "Firebase users update own progress"
  on reading_progress for update
  using (
    (auth.jwt() ->> 'role') = 'authenticated'
    and user_id = (auth.jwt() ->> 'sub')
  )
  with check (
    (auth.jwt() ->> 'role') = 'authenticated'
    and user_id = (auth.jwt() ->> 'sub')
  );

drop policy if exists "Public reads approved comments" on essay_comments;
drop policy if exists "Auth users insert comments" on essay_comments;
drop policy if exists "Users delete own comments" on essay_comments;
drop policy if exists "Anyone authenticated can update approval" on essay_comments;
drop policy if exists "Public reads approved comments and admins read pending" on essay_comments;
drop policy if exists "Firebase users insert pending comments" on essay_comments;
drop policy if exists "Owners or admins delete comments" on essay_comments;
drop policy if exists "Firebase admins update comments" on essay_comments;

create policy "Public reads approved comments and admins read pending"
  on essay_comments for select
  using (
    approved = true
    or (
      (auth.jwt() ->> 'role') = 'authenticated'
      and (auth.jwt() ->> 'admin') = 'true'
    )
  );

create policy "Firebase users insert pending comments"
  on essay_comments for insert
  with check (
    (auth.jwt() ->> 'role') = 'authenticated'
    and user_id = (auth.jwt() ->> 'sub')
    and coalesce(approved, false) = false
  );

create policy "Owners or admins delete comments"
  on essay_comments for delete
  using (
    (
      (auth.jwt() ->> 'role') = 'authenticated'
      and user_id = (auth.jwt() ->> 'sub')
    )
    or (
      (auth.jwt() ->> 'role') = 'authenticated'
      and (auth.jwt() ->> 'admin') = 'true'
    )
  );

create policy "Firebase admins update comments"
  on essay_comments for update
  using (
    (auth.jwt() ->> 'role') = 'authenticated'
    and (auth.jwt() ->> 'admin') = 'true'
  )
  with check (
    (auth.jwt() ->> 'role') = 'authenticated'
    and (auth.jwt() ->> 'admin') = 'true'
  );

-- Essay view counts remain public and do not depend on authentication.
create table if not exists essay_views (
  slug        text primary key,
  view_count  integer not null default 0
);

alter table essay_views enable row level security;
drop policy if exists "Public reads essay views" on essay_views;
create policy "Public reads essay views"
  on essay_views for select
  using (true);

create or replace function increment_essay_view(essay_slug text)
returns void
language plpgsql
security definer
as $$
begin
  insert into essay_views (slug, view_count)
  values (essay_slug, 1)
  on conflict (slug)
  do update set view_count = essay_views.view_count + 1;
end;
$$;

create index if not exists idx_reading_progress_user on reading_progress(user_id);
create index if not exists idx_essay_comments_slug on essay_comments(slug, approved);
