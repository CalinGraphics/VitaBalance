-- Aliniere a bazei de date cu aplicația (autentificare email + parolă) și întărire a securității.
-- Idempotent: poate fi rulat de mai multe ori.

-- 1) Comentarii aliniate cu noul flux de autentificare
comment on table public.users is
  'Profil utilizator: identitate (email, name), antropometrie, dietă, alergii; autentificare cu email + parolă (bcrypt).';
comment on column public.users.email is
  'Email unic (litere mici); identifică utilizatorul la login și în claim-ul email din JWT.';
comment on column public.users.password_hash is
  'Hash bcrypt al parolei, necesar la login. NULL = cont creat înainte de trecerea la parolă (fost magic link), fără parolă setată.';
comment on table public.magic_links is
  'DEPRECAT: aplicația nu mai folosește magic link. Se șterge cu 002_drop_magic_links.sql.';

-- 2) Unicitate email indiferent de majuscule/minuscule (users_email_key e sensibil la majuscule)
create unique index if not exists users_email_lower_key on public.users (lower(email));

-- 3) search_path fix pe funcțiile trigger (lint function_search_path_mutable)
alter function public.update_updated_at_column()            set search_path = public, pg_temp;
alter function public.lab_results_set_user_email()          set search_path = public, pg_temp;
alter function public.users_propagate_email_to_lab_results() set search_path = public, pg_temp;
alter function public.lab_results_touch_updated_at()        set search_path = public, pg_temp;

-- 4) Backend-ul accesează baza exclusiv cu cheia service_role (ocolește RLS); frontend-ul nu folosește Supabase direct.
--    Retragem drepturile rolurilor publice: tabelele nu mai apar în schema GraphQL/REST pentru anon/authenticated.
--    (RLS rămâne activ, fără politici = acces interzis pentru aceste roluri.)
revoke all on all tables    in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;
revoke all on all functions in schema public from anon, authenticated;
alter default privileges in schema public revoke all on tables    from anon, authenticated;
alter default privileges in schema public revoke all on sequences from anon, authenticated;
alter default privileges in schema public revoke all on functions from anon, authenticated;

-- Revenire (dacă ai nevoie de acces direct prin anon/authenticated, adaugă mai întâi politici RLS):
--   grant select on all tables in schema public to anon, authenticated;
