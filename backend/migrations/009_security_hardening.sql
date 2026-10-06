-- Întărirea securității după auditul Supabase (6 oct. 2026). Idempotent.
--
-- 1) Profilele vechi fără cont (create pe vremea magic link) NU mai sunt adoptate automat la înregistrare:
--    contul se crea direct confirmat, fără verificarea emailului, deci oricine știa adresa vedea datele
--    medicale ale proprietarului. Adopția cere acum aprobarea unui admin (legacy_adoption_approved_at).
-- 2) Profilul se creează / se leagă doar pentru conturi cu emailul confirmat. Un cont creat neconfirmat
--    (ex. prin /auth/v1/signup) primește profil abia la confirmare.
-- 3) Rolul authenticated nu mai are drepturi de citire directă: aplicația trece doar prin backend
--    (service_role). Politicile *_select_own rămân ca a doua linie de apărare.
-- 4) Funcțiile-trigger nu mai pot fi executate de rolurile API.
-- 5) Index fără nicio interogare care să-l folosească.

-- 1) aprobarea adopției unui profil vechi
alter table public.users add column if not exists legacy_adoption_approved_at timestamptz;

comment on column public.users.legacy_adoption_approved_at is
  'Setat de un admin după verificarea identității: permite ca profilul vechi (auth_user_id NULL) să fie preluat la înregistrarea cu același email. NULL = înregistrarea pe acest email e respinsă.';

-- 1 + 2) triggerul auth.users -> profil
create or replace function public.handle_auth_user_created()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_email   text := lower(trim(new.email));
  v_name    text := nullif(trim(coalesce(new.raw_user_meta_data ->> 'full_name', '')), '');
  v_profile public.users%rowtype;
begin
  -- Conturile neconfirmate nu ating public.users (se leagă la confirmare, prin on_auth_user_confirmed).
  if new.email_confirmed_at is null or v_email is null or v_email = '' then
    return new;
  end if;

  select * into v_profile from public.users where lower(email) = v_email;

  if not found then
    insert into public.users (email, name, auth_user_id) values (v_email, coalesce(v_name, ''), new.id);
    return new;
  end if;

  if v_profile.auth_user_id is not null then
    raise exception 'Profilul pentru % e deja legat de un cont', v_email using errcode = '23505';
  end if;

  if v_profile.legacy_adoption_approved_at is null then
    raise exception 'Profil vechi blocat pentru %: adopția cere aprobarea unui admin', v_email
      using errcode = '42501';
  end if;

  update public.users
     set auth_user_id = new.id,
         name = coalesce(nullif(trim(name), ''), v_name, '')
   where id = v_profile.id;
  return new;
end;
$$;

revoke all on function public.handle_auth_user_created() from public, anon, authenticated;

drop trigger if exists on_auth_user_confirmed on auth.users;
create trigger on_auth_user_confirmed
  after update of email_confirmed_at on auth.users
  for each row
  when (old.email_confirmed_at is null and new.email_confirmed_at is not null)
  execute function public.handle_auth_user_created();

-- 3) fără citire directă pentru authenticated
revoke select on public.users, public.foods, public.lab_results, public.recommendations, public.feedback
  from authenticated;

-- 4) funcțiile-trigger nu sunt API
revoke execute on function
  public.lab_results_set_user_email(),
  public.lab_results_touch_updated_at(),
  public.update_updated_at_column(),
  public.users_propagate_email_to_lab_results()
  from public, anon, authenticated;

-- 5) index nefolosit
drop index if exists public.idx_foods_name;
