-- Poza de profil: fișierul stă în Supabase Storage (bucket privat `avatars`), calea lui în users.avatar_path.
-- Doar backend-ul (service_role) scrie și citește fișierele: storage.objects are RLS activ și nicio politică
-- pentru anon/authenticated, iar clientul primește un link semnat, cu durată limitată. Idempotent.

alter table public.users add column if not exists avatar_path text;

comment on column public.users.avatar_path is
  'Calea pozei de profil în bucket-ul privat `avatars` (ex. <auth_user_id>/<uuid>.webp). NULL = fără poză.';

-- users.updated_at decide când sunt regenerate recomandările (sync-meta). Schimbarea pozei nu trebuie să le
-- invalideze, deci triggerul lasă updated_at neschimbat dacă s-a modificat doar avatar_path.
create or replace function public.users_touch_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if new.avatar_path is distinct from old.avatar_path
     and (to_jsonb(new) - 'avatar_path' - 'updated_at') = (to_jsonb(old) - 'avatar_path' - 'updated_at') then
    new.updated_at := old.updated_at;
  else
    new.updated_at := now();
  end if;
  return new;
end;
$$;

revoke all on function public.users_touch_updated_at() from public, anon, authenticated;

drop trigger if exists update_users_updated_at on public.users;
create trigger update_users_updated_at
  before update on public.users
  for each row execute function public.users_touch_updated_at();

-- Funcția generică nu mai era folosită de niciun alt tabel.
drop function if exists public.update_updated_at_column();

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('avatars', 'avatars', false, 2097152, array['image/jpeg', 'image/png', 'image/webp'])
on conflict (id) do update
  set public = excluded.public,
      file_size_limit = excluded.file_size_limit,
      allowed_mime_types = excluded.allowed_mime_types;
