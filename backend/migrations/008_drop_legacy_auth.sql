-- Curățenie după trecerea pe Supabase Auth (007): parolele stau în auth.users, magic link nu mai există.
-- Condiție verificată înainte de aplicare (a întors 0):
--   select count(*) from public.users where password_hash is not null and auth_user_id is null;

alter table public.users drop column if exists password_hash;

-- Înlocuiește 002_drop_magic_links.sql.
drop table if exists public.magic_links;
