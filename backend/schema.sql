-- =============================================================================
-- VitaBalance — schema completă (PostgreSQL / Supabase, schema `public`)
-- =============================================================================
-- Starea țintă după migrările 001–015 (magic_links și users.password_hash eliminate). Pentru o bază NOUĂ rulează doar acest fișier;
-- pentru baza existentă aplică migrările din backend/migrations/ în ordine. Actualizează fișierul la fiecare migrare.
--
-- Autentificare: Supabase Auth. Emailul și parola (bcrypt) stau în auth.users; public.users e profilul aplicației,
-- legat prin auth_user_id și creat de triggerul on_auth_user_created doar pentru conturi confirmate. Un profil vechi
-- fără cont se preia numai după aprobarea unui admin (legacy_adoption_approved_at, migrarea 009).
-- Acces: doar backend-ul, cu cheia service_role (ocolește RLS); vorbește cu Supabase Auth pentru login/sesiune.
-- anon și authenticated nu au drepturi pe tabele; politicile *_select_own rămân ca a doua linie de apărare.
-- Catalogul validat de alimente e în repo (data/foods_catalog.json -> migrarea 012); conturile de test doar în baza de date.
-- =============================================================================

-- ---------- users ----------
create table public.users (
  id                 serial primary key,
  email              varchar(255) not null unique,            -- litere mici; vezi și users_email_lower_key
  auth_user_id       uuid unique references auth.users (id) on delete set null, -- contul Supabase Auth; NULL = profil vechi fără parolă
  name               varchar(255),
  age                integer,
  sex                varchar(10),
  weight             double precision,                        -- kg
  height             double precision,                        -- cm
  activity_level     varchar(50),
  diet_type          varchar(50),
  allergies          text,                                    -- valori separate prin virgulă (vezi frontend allergies.ts)
  medical_conditions text,                                    -- coduri separate prin virgulă (medicalConditions.ts)
  caloric_goal       numeric,                                 -- kcal/zi, opțional, doar informativ
  rec_refresh_status text not null default 'idle',            -- idle | pending | done | failed
  rec_refresh_error  text,
  rec_refresh_at     timestamptz,
  legacy_adoption_approved_at timestamptz,                    -- aprobarea adminului pentru preluarea unui profil vechi
  avatar_path        text,                                    -- poza de profil în bucket-ul privat `avatars`
  created_at         timestamptz default now(),
  updated_at         timestamptz default now(),
  constraint users_sex_check            check (sex is null or sex in ('F', 'M', 'other')),
  constraint users_activity_level_check check (activity_level is null or activity_level in ('sedentary', 'moderate', 'active', 'very_active')),
  constraint users_diet_type_check      check (diet_type is null or diet_type in ('omnivore', 'vegetarian', 'vegan', 'pescatarian')),
  constraint users_body_metrics_range   check (
    (age is null or age between 1 and 120)
    and (weight is null or weight between 20 and 400)
    and (height is null or height between 50 and 260)
  ),
  constraint users_caloric_goal_range   check (caloric_goal is null or (caloric_goal >= 500 and caloric_goal <= 10000))
);
create unique index users_email_lower_key on public.users (lower(email));

comment on table  public.users is 'Profil utilizator (antropometrie, dietă, alergii). Credențialele (email + parolă) sunt în auth.users, legat prin auth_user_id.';
comment on column public.users.email is 'Email unic (litere mici), sincronizat din auth.users.email.';
comment on column public.users.auth_user_id is 'FK auth.users.id: contul Supabase Auth (email + parolă) al acestui profil. NULL = profil vechi fără parolă, se leagă la înregistrare.';
comment on column public.users.legacy_adoption_approved_at is 'Setat de un admin după verificarea identității: permite ca profilul vechi (auth_user_id NULL) să fie preluat la înregistrarea cu același email. NULL = înregistrarea pe acest email e respinsă.';
comment on column public.users.caloric_goal is 'Obiectiv caloric zilnic (kcal), opțional; informativ, nu influențează recomandările.';

-- ---------- foods (catalog; valori per 100 g, NULL = necunoscut) ----------
-- Catalogul validat (validated = true) vine din USDA FoodData Central: migrarea 012, generată de
-- scripts/build_food_catalog.py. Rândurile vechi rămân pentru FK-uri, dar nu mai sunt recomandate.
create table public.foods (
  id          serial primary key,                             -- cheie stabilă; nu se renumerotează
  food_key    text,                                           -- cheie din data/food_catalog_spec.py (NULL = catalog vechi)
  fdc_id      integer,                                        -- ID USDA FoodData Central
  data_source text,                                           -- ex. usda_sr_legacy_2018
  validated   boolean not null default false,                 -- doar acestea sunt recomandate
  name        varchar(255) not null,                          -- română (implicit)
  name_en     text,                                           -- engleză; NULL = netradus (se afișează name)
  category    varchar(100),                                   -- eticheta RO a categoriei
  category_key text,                                          -- nuts, seeds, legumes, ... (diversitate, alternative)
  portion_g   double precision,                               -- porția realistă (g sau ml)
  portion_label_ro text,
  portion_label_en text,
  animal_source text,                                         -- dairy | egg | fish | shellfish | meat | poultry | NULL
  allergen_codes text[] not null default '{}',                -- aceleași coduri ca users.allergies
  flags       text[] not null default '{}',                   -- raw_animal, high_mercury, liver, ...
  iron        double precision,
  calcium     double precision,
  vitamin_d   double precision,                               -- µg
  vitamin_b12 double precision,
  magnesium   double precision,
  protein     double precision,
  zinc        double precision,
  vitamin_c   double precision,
  fiber       double precision,
  calories    double precision,
  folate      double precision,                               -- µg DFE
  vitamin_a   double precision,                               -- µg RAE
  iodine      double precision,
  vitamin_k   double precision,
  potassium   double precision,
  phosphorus  double precision,
  sodium      double precision,
  sugars      double precision,
  alcohol     double precision,
  allergens   text,
  carbs       double precision,
  fat         double precision,
  free_sugar  double precision,
  cholesterol double precision,
  created_at  timestamptz default now(),
  constraint foods_animal_source_check check (animal_source is null or animal_source in ('dairy', 'egg', 'fish', 'shellfish', 'meat', 'poultry')),
  constraint foods_validated_requires_source check (not validated or (fdc_id is not null and data_source is not null and portion_g > 0 and category_key is not null))
);
create index idx_foods_category on public.foods (category);
create unique index uq_foods_food_key on public.foods (food_key) where food_key is not null;
create index idx_foods_validated on public.foods (id) where validated;

comment on table public.foods is
  'Catalog alimente. Rândurile cu validated = true au valori la 100 g din USDA FoodData Central (NULL = necunoscut).';

-- ---------- wellbeing_checkins (jurnal zilnic de stare; un rând pe zi) ----------
create table public.wellbeing_checkins (
  id          bigserial primary key,
  user_id     integer not null references public.users (id) on delete cascade,
  checked_on  date not null default current_date,
  symptoms    text[] not null default '{}',
  severity    smallint,
  energy      smallint,
  weight      double precision,
  notes       text,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  constraint wellbeing_checkins_user_day_key unique (user_id, checked_on),
  constraint wellbeing_checkins_symptoms_check check (symptoms <@ array[
    'greata', 'varsaturi', 'ameteli', 'oboseala', 'dureri_cap', 'crampe_musculare',
    'constipatie', 'diaree', 'balonare', 'arsuri', 'lipsa_poftei'
  ]::text[]),
  constraint wellbeing_checkins_severity_check check (severity is null or severity between 1 and 3),
  constraint wellbeing_checkins_energy_check check (energy is null or energy between 1 and 5),
  constraint wellbeing_checkins_weight_check check (weight is null or weight between 20 and 400),
  constraint wellbeing_checkins_notes_length check (notes is null or char_length(notes) <= 1000)
);

create index idx_wellbeing_checkins_user_day on public.wellbeing_checkins (user_id, checked_on desc);


-- ---------- lab_results (istoric analize; mai multe rânduri per utilizator) ----------
create table public.lab_results (
  id          serial primary key,
  user_id     integer not null references public.users (id) on delete cascade,
  user_email  text not null,                                  -- denormalizat din users (trigger)
  hemoglobin  double precision,
  ferritin    double precision,
  vitamin_d   double precision,
  vitamin_b12 double precision,
  calcium     double precision,
  magnesium   double precision,
  zinc        double precision,
  protein     double precision,
  folate      double precision,
  vitamin_a   double precision,
  vitamin_c   double precision,
  iodine      double precision,
  vitamin_k   double precision,
  potassium   double precision,
  notes       text,
  created_at  timestamptz default now(),
  updated_at  timestamptz not null default now()
);
create index idx_lab_results_user_latest on public.lab_results (user_id, updated_at desc, created_at desc);

-- ---------- recommendations (recomandări materializate) ----------
create table public.recommendations (
  id                  serial primary key,
  user_id             integer not null references public.users (id) on delete cascade,
  food_id             integer not null references public.foods (id) on delete cascade,
  score               double precision not null,
  explanation         text not null,
  portion_suggested   double precision,
  coverage_percentage double precision,
  explanation_json    jsonb,                                  -- text, portion, reasons, tips, alternatives
  reasons             text[] default '{}',
  tips                text[] default '{}',
  created_at          timestamptz default now()
);
create index idx_recommendations_food_id       on public.recommendations (food_id);
create index idx_recommendations_user_created  on public.recommendations (user_id, created_at desc);
create index idx_recommendations_user_score    on public.recommendations (user_id, score desc, id);

-- ---------- feedback (persistent per utilizator + aliment) ----------
create table public.feedback (
  id                serial primary key,
  user_id           integer not null references public.users (id) on delete cascade,
  food_id           integer not null references public.foods (id) on delete cascade,
  recommendation_id integer references public.recommendations (id) on delete set null,
  rating            integer,
  created_at        timestamptz default now(),
  constraint feedback_rating_check check (rating >= -1 and rating <= 5)
);
create unique index uq_feedback_user_food         on public.feedback (user_id, food_id);
create index        idx_feedback_food_id          on public.feedback (food_id) where food_id is not null;
create index        idx_feedback_recommendation_id on public.feedback (recommendation_id);

comment on table public.feedback is 'Apreciere (rating) a utilizatorului pentru un aliment; unică per (user_id, food_id) și persistă când recomandarea e regenerată/ștearsă.';
comment on column public.feedback.recommendation_id is 'Recomandarea curentă asociată (opțional); devine NULL când recomandarea este ștearsă, feedback-ul rămâne.';

-- ---------- funcții și trigger-e ----------
-- updated_at decide când sunt regenerate recomandările; schimbarea pozei nu trebuie să le invalideze.
create or replace function public.users_touch_updated_at() returns trigger
language plpgsql set search_path = '' as $$
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

create or replace function public.lab_results_touch_updated_at() returns trigger
language plpgsql set search_path = public, pg_temp as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

create or replace function public.lab_results_set_user_email() returns trigger
language plpgsql set search_path = public, pg_temp as $$
begin
  select u.email into strict new.user_email from public.users u where u.id = new.user_id;
  return new;
exception
  when no_data_found then
    raise exception 'lab_results: user_id % inexistent în users', new.user_id using errcode = '23503';
end;
$$;

create or replace function public.users_propagate_email_to_lab_results() returns trigger
language plpgsql set search_path = public, pg_temp as $$
begin
  if new.email is distinct from old.email then
    update public.lab_results set user_email = new.email where user_id = new.id;
  end if;
  return new;
end;
$$;

create trigger update_users_updated_at          before update on public.users
  for each row execute function public.users_touch_updated_at();
create trigger trg_users_email_lab_results      after update of email on public.users
  for each row execute function public.users_propagate_email_to_lab_results();
create trigger trg_lab_results_set_user_email   before insert or update on public.lab_results
  for each row execute function public.lab_results_set_user_email();
create trigger trg_lab_results_touch_updated_at before update on public.lab_results
  for each row execute function public.lab_results_touch_updated_at();

-- ---------- Supabase Auth -> profil ----------
create or replace function public.handle_auth_user_created()
returns trigger language plpgsql security definer set search_path = '' as $$
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
    raise exception 'Profil vechi blocat pentru %: adopția cere aprobarea unui admin', v_email using errcode = '42501';
  end if;
  update public.users
     set auth_user_id = new.id,
         name = coalesce(nullif(trim(name), ''), v_name, '')
   where id = v_profile.id;
  return new;
end;
$$;

create or replace function public.handle_auth_user_email_changed()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  if new.email is distinct from old.email and new.email is not null then
    update public.users set email = lower(trim(new.email)) where auth_user_id = new.id;
  end if;
  return new;
end;
$$;

create trigger on_auth_user_created       after insert on auth.users
  for each row execute function public.handle_auth_user_created();
create trigger on_auth_user_confirmed     after update of email_confirmed_at on auth.users
  for each row when (old.email_confirmed_at is null and new.email_confirmed_at is not null)
  execute function public.handle_auth_user_created();
create trigger on_auth_user_email_changed after update of email on auth.users
  for each row execute function public.handle_auth_user_email_changed();

-- ---------- securitate ----------
alter table public.users           enable row level security;
alter table public.foods           enable row level security;
alter table public.wellbeing_checkins enable row level security;
alter table public.lab_results     enable row level security;
alter table public.recommendations enable row level security;
alter table public.feedback        enable row level security;

revoke all on all tables    in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;
revoke all on all functions in schema public from public, anon, authenticated;
alter default privileges in schema public revoke all on tables    from anon, authenticated;
alter default privileges in schema public revoke all on sequences from anon, authenticated;
alter default privileges in schema public revoke all on functions from anon, authenticated;

-- Politici de citire pentru authenticated, fără GRANT: aplicația nu citește direct din Supabase (migrarea 009).
-- Rămân ca a doua linie de apărare dacă cineva acordă vreodată SELECT acestui rol.

create policy users_select_own on public.users for select to authenticated
  using (auth_user_id = (select auth.uid()));
create policy foods_select_all on public.foods for select to authenticated
  using (true);
create policy lab_results_select_own on public.lab_results for select to authenticated
  using (user_id in (select u.id from public.users u where u.auth_user_id = (select auth.uid())));
create policy recommendations_select_own on public.recommendations for select to authenticated
  using (user_id in (select u.id from public.users u where u.auth_user_id = (select auth.uid())));
create policy feedback_select_own on public.feedback for select to authenticated
  using (user_id in (select u.id from public.users u where u.auth_user_id = (select auth.uid())));

-- ---------- Storage: poze de profil ----------
-- Bucket privat; doar backend-ul (service_role) scrie și citește. storage.objects are RLS activ, fără politici
-- pentru anon/authenticated, iar clientul primește linkuri semnate, temporare.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('avatars', 'avatars', false, 2097152, array['image/jpeg', 'image/png', 'image/webp'])
on conflict (id) do nothing;
