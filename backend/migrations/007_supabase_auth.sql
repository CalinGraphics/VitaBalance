-- Autentificarea trece pe Supabase Auth: emailul și parola stau în auth.users (bcrypt, gestionat de
-- Supabase), iar sesiunea e tokenul emis de Supabase. Backend-ul nu mai semnează tokenuri proprii
-- (dispare JWT_SECRET). public.users rămâne profilul aplicației, legat 1:1 de auth.users.
-- Idempotent.

-- 1) Legătura profil -> cont Supabase Auth.
alter table public.users add column if not exists auth_user_id uuid;

alter table public.users drop constraint if exists users_auth_user_id_fkey;
alter table public.users add constraint users_auth_user_id_fkey
  foreign key (auth_user_id) references auth.users (id) on delete set null;

create unique index if not exists users_auth_user_id_key on public.users (auth_user_id);

comment on column public.users.auth_user_id is
  'FK auth.users.id: contul Supabase Auth (email + parolă) al acestui profil. NULL = profil vechi fără parolă, se leagă la înregistrare.';

-- 2) Contul nou din auth.users -> profil în public.users.
--    Dacă există deja un profil nelegat cu același email (cont vechi, fost magic link), îl adoptă:
--    utilizatorul își păstrează profilul, analizele și recomandările.
create or replace function public.handle_auth_user_created()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_email text := lower(trim(new.email));
  v_name  text := nullif(trim(coalesce(new.raw_user_meta_data ->> 'full_name', '')), '');
begin
  if v_email is null or v_email = '' then
    return new;
  end if;

  update public.users
     set auth_user_id = new.id,
         name = coalesce(nullif(trim(name), ''), v_name, '')
   where lower(email) = v_email
     and auth_user_id is null;

  if not found then
    -- Emailul e unic în public.users: dacă profilul e deja legat de alt cont, inserarea eșuează
    -- și odată cu ea crearea contului (nu legăm două conturi de același profil).
    insert into public.users (email, name, auth_user_id)
    values (v_email, coalesce(v_name, ''), new.id);
  end if;

  return new;
end;
$$;

-- 3) Schimbarea emailului în Supabase Auth se propagă în profil (și de acolo în lab_results.user_email).
create or replace function public.handle_auth_user_email_changed()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if new.email is distinct from old.email and new.email is not null then
    update public.users set email = lower(trim(new.email)) where auth_user_id = new.id;
  end if;
  return new;
end;
$$;

revoke all on function public.handle_auth_user_created() from public, anon, authenticated;
revoke all on function public.handle_auth_user_email_changed() from public, anon, authenticated;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_auth_user_created();

drop trigger if exists on_auth_user_email_changed on auth.users;
create trigger on_auth_user_email_changed
  after update of email on auth.users
  for each row execute function public.handle_auth_user_email_changed();

-- 4) Conturile existente cu parolă trec în auth.users cu hash-ul bcrypt păstrat, deci parolele
--    actuale continuă să funcționeze. Triggerul de mai sus leagă fiecare profil.
--    Coloanele *_token trebuie să fie '' (nu NULL), altfel GoTrue nu poate citi rândul.
insert into auth.users (
  instance_id, id, aud, role, email, encrypted_password, email_confirmed_at,
  raw_app_meta_data, raw_user_meta_data, created_at, updated_at,
  confirmation_token, recovery_token, email_change_token_new, email_change,
  email_change_token_current, phone_change, phone_change_token, reauthentication_token
)
select
  '00000000-0000-0000-0000-000000000000', gen_random_uuid(), 'authenticated', 'authenticated',
  lower(u.email), u.password_hash, now(),
  '{"provider":"email","providers":["email"]}'::jsonb,
  jsonb_build_object('full_name', coalesce(u.name, '')),
  coalesce(u.created_at, now()), now(),
  '', '', '', '', '', '', '', ''
from public.users u
where u.password_hash is not null
  and u.auth_user_id is null
  and not exists (select 1 from auth.users a where lower(a.email) = lower(u.email));

insert into auth.identities (provider_id, user_id, identity_data, provider, last_sign_in_at, created_at, updated_at)
select
  a.id::text, a.id,
  jsonb_build_object('sub', a.id::text, 'email', a.email, 'email_verified', true, 'phone_verified', false),
  'email', null, a.created_at, now()
from auth.users a
where not exists (select 1 from auth.identities i where i.user_id = a.id and i.provider = 'email');

-- 5) Acces direct din Supabase (rolul authenticated, cu tokenul utilizatorului): doar citire, doar
--    rândurile proprii. Backend-ul folosește service_role și nu e afectat; scrierile rămân prin API.
grant usage on schema public to authenticated;

grant select (id, email, name, age, sex, weight, height, activity_level, diet_type, allergies,
              medical_conditions, caloric_goal, created_at, updated_at, auth_user_id)
  on public.users to authenticated;
grant select on public.foods, public.lab_results, public.recommendations, public.feedback to authenticated;

drop policy if exists users_select_own on public.users;
create policy users_select_own on public.users
  for select to authenticated
  using (auth_user_id = (select auth.uid()));

drop policy if exists foods_select_all on public.foods;
create policy foods_select_all on public.foods
  for select to authenticated
  using (true);

drop policy if exists lab_results_select_own on public.lab_results;
create policy lab_results_select_own on public.lab_results
  for select to authenticated
  using (user_id in (select u.id from public.users u where u.auth_user_id = (select auth.uid())));

drop policy if exists recommendations_select_own on public.recommendations;
create policy recommendations_select_own on public.recommendations
  for select to authenticated
  using (user_id in (select u.id from public.users u where u.auth_user_id = (select auth.uid())));

drop policy if exists feedback_select_own on public.feedback;
create policy feedback_select_own on public.feedback
  for select to authenticated
  using (user_id in (select u.id from public.users u where u.auth_user_id = (select auth.uid())));

comment on table public.users is
  'Profil utilizator (antropometrie, dietă, alergii). Credențialele (email + parolă) sunt în auth.users, legat prin auth_user_id.';
comment on column public.users.email is
  'Email unic (litere mici), sincronizat din auth.users.email.';
comment on column public.users.password_hash is
  'DEPRECAT: parolele sunt în auth.users. Păstrat doar cât timp producția veche (main) mai citește coloana; se șterge cu 008.';
