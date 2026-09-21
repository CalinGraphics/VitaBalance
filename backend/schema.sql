-- =============================================================================
-- VitaBalance — schema completă (PostgreSQL / Supabase, schema `public`)
-- =============================================================================
-- Starea țintă după migrările 001–006 + 002 (magic_links eliminat). Pentru o bază NOUĂ rulează doar acest fișier;
-- pentru baza existentă aplică migrările din backend/migrations/ în ordine. Actualizează fișierul la fiecare migrare.
--
-- Acces: backend-ul folosește exclusiv cheia service_role (ocolește RLS). RLS e activ FĂRĂ politici, iar rolurile
-- anon/authenticated nu au drepturi pe tabele: frontend-ul nu accesează Supabase direct.
-- Date de referință (catalogul `foods` și conturile de test) trăiesc doar în baza de date, nu în repo.
-- =============================================================================

-- ---------- users ----------
create table public.users (
  id                 serial primary key,
  email              varchar(255) not null unique,            -- litere mici; vezi și users_email_lower_key
  password_hash      text,                                    -- bcrypt; NULL = cont vechi (magic link) fără parolă
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

comment on table  public.users is 'Profil utilizator: identitate (email, name), antropometrie, dietă, alergii; autentificare cu email + parolă (bcrypt).';
comment on column public.users.email is 'Email unic (litere mici); identifică utilizatorul la login și în claim-ul email din JWT.';
comment on column public.users.password_hash is 'Hash bcrypt al parolei, necesar la login. NULL = cont creat înainte de trecerea la parolă, fără parolă setată.';
comment on column public.users.caloric_goal is 'Obiectiv caloric zilnic (kcal), opțional; informativ, nu influențează recomandările.';

-- ---------- foods (catalog; valori per 100 g) ----------
create table public.foods (
  id          serial primary key,                             -- cheie stabilă; nu se renumerotează
  name        varchar(255) not null,                          -- română (implicit)
  name_en     text,                                           -- engleză; NULL = netradus (se afișează name)
  category    varchar(100),
  iron        double precision default 0,
  calcium     double precision default 0,
  vitamin_d   double precision default 0,
  vitamin_b12 double precision default 0,
  magnesium   double precision default 0,
  protein     double precision default 0,
  zinc        double precision default 0,
  vitamin_c   double precision default 0,
  fiber       double precision default 0,
  calories    double precision default 0,
  folate      double precision default 0,
  vitamin_a   double precision default 0,
  iodine      double precision default 0,
  vitamin_k   double precision default 0,
  potassium   double precision default 0,
  allergens   text,
  carbs       double precision not null default 0,
  fat         double precision not null default 0,
  free_sugar  double precision not null default 0,
  cholesterol double precision not null default 0,
  created_at  timestamptz default now()
);
create index idx_foods_category on public.foods (category);
create index idx_foods_name     on public.foods (name);

comment on table public.foods is 'Catalog nutrienți per 100 g; id este cheie stabilă (nu se renumără la 1..N fără migrare de FK-uri).';

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
create index idx_lab_results_user_id on public.lab_results (user_id);

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
create or replace function public.update_updated_at_column() returns trigger
language plpgsql set search_path = public, pg_temp as $$
begin
  new.updated_at = now();
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
  for each row execute function public.update_updated_at_column();
create trigger trg_users_email_lab_results      after update of email on public.users
  for each row execute function public.users_propagate_email_to_lab_results();
create trigger trg_lab_results_set_user_email   before insert or update on public.lab_results
  for each row execute function public.lab_results_set_user_email();
create trigger trg_lab_results_touch_updated_at before update on public.lab_results
  for each row execute function public.lab_results_touch_updated_at();

-- ---------- securitate ----------
alter table public.users           enable row level security;
alter table public.foods           enable row level security;
alter table public.lab_results     enable row level security;
alter table public.recommendations enable row level security;
alter table public.feedback        enable row level security;

revoke all on all tables    in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;
revoke all on all functions in schema public from anon, authenticated;
alter default privileges in schema public revoke all on tables    from anon, authenticated;
alter default privileges in schema public revoke all on sequences from anon, authenticated;
alter default privileges in schema public revoke all on functions from anon, authenticated;
