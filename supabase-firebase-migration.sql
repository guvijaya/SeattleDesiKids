-- Upgrade an existing Supabase schema before deploying Firebase-authenticated clients.
-- Back up the database and review this file before running it in the Supabase SQL editor.
begin;

-- Firebase UIDs are strings, and they have no row in Supabase auth.users.
-- Preserve each existing UUID verbatim as text; do not infer Firebase identities here.
alter table reading_progress
  drop constraint if exists reading_progress_user_id_fkey;
alter table essay_comments
  drop constraint if exists essay_comments_user_id_fkey;
alter table reading_progress
  alter column user_id type text using user_id::text;
alter table essay_comments
  alter column user_id type text using user_id::text;

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

commit;

-- Optional, manual identity mapping. Use only a verified, trusted mapping from an
-- authenticated user linking process; never map by email alone. Leave historical
-- UUID identities unchanged when no reliable mapping exists.
--
-- begin;
-- create temporary table firebase_uid_mapping (
--   supabase_user_id uuid primary key,
--   firebase_uid text not null unique
-- ) on commit drop;
-- insert into firebase_uid_mapping values ('<verified-supabase-uuid>', '<verified-firebase-uid>');
--
-- Check for progress collisions before updating. Resolve them deliberately without
-- deleting either row; the UPDATE will fail safely while the unique key conflicts.
-- select old.user_id as old_user_id, old.slug, mapping.firebase_uid
-- from reading_progress old
-- join firebase_uid_mapping mapping on old.user_id = mapping.supabase_user_id::text
-- join reading_progress existing
--   on existing.user_id = mapping.firebase_uid and existing.slug = old.slug;
--
-- update reading_progress rows
-- set user_id = mapping.firebase_uid
-- from firebase_uid_mapping mapping
-- where reading_progress.user_id = mapping.supabase_user_id::text;
-- update essay_comments rows
-- set user_id = mapping.firebase_uid
-- from firebase_uid_mapping mapping
-- where essay_comments.user_id = mapping.supabase_user_id::text;
-- commit;
