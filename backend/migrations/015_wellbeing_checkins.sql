-- 015: jurnalul de stare al utilizatorului (simptome, energie, greutate) pentru urmărirea progresului.
-- Un rând pe zi și utilizator (upsert pe user_id + checked_on). Doar backend-ul (service_role) citește și scrie:
-- RLS activ, fără politici, fără drepturi pentru anon/authenticated (ca restul tabelelor cu date de utilizator, 009).
-- Idempotent.

begin;

create table if not exists public.wellbeing_checkins (
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

create index if not exists idx_wellbeing_checkins_user_day on public.wellbeing_checkins (user_id, checked_on desc);

alter table public.wellbeing_checkins enable row level security;
revoke all on public.wellbeing_checkins from anon, authenticated;

comment on table public.wellbeing_checkins is
  'Jurnal zilnic de stare: simptome (coduri din backend/rules/symptoms.py), severitate 1-3, energie 1-5, greutate. Un rând pe zi.';
comment on column public.wellbeing_checkins.symptoms is 'Coduri de simptome; influențează recomandările doar 14 zile.';

commit;
