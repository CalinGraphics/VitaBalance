-- 011: schema pentru catalogul validat de alimente (date USDA, porții realiste, marcaje de siguranță).
--
-- Alimentele vechi (591) rămân în tabel, pentru că recomandările și voturile vechi le referă prin FK, dar au
-- validated = false și motorul nu le mai recomandă. Catalogul nou se încarcă din 012_seed_validated_foods.sql.
-- Idempotent. Nu atinge RLS: `foods` are deja RLS activ, fără acces pentru anon/authenticated (009).

begin;

alter table public.foods
  add column if not exists food_key text,
  add column if not exists fdc_id integer,
  add column if not exists data_source text,
  add column if not exists validated boolean not null default false,
  add column if not exists category_key text,
  add column if not exists portion_g double precision,
  add column if not exists portion_label_ro text,
  add column if not exists portion_label_en text,
  add column if not exists animal_source text,
  add column if not exists allergen_codes text[] not null default '{}',
  add column if not exists flags text[] not null default '{}',
  add column if not exists sugars double precision,
  add column if not exists alcohol double precision,
  add column if not exists phosphorus double precision,
  add column if not exists sodium double precision;

-- O valoare lipsă trebuie să rămână NULL („nu știm”), nu 0 („nu conține”).
alter table public.foods
  alter column iron drop default, alter column calcium drop default, alter column vitamin_d drop default,
  alter column vitamin_b12 drop default, alter column magnesium drop default, alter column protein drop default,
  alter column zinc drop default, alter column vitamin_c drop default, alter column fiber drop default,
  alter column calories drop default, alter column folate drop default, alter column vitamin_a drop default,
  alter column iodine drop default, alter column vitamin_k drop default, alter column potassium drop default,
  alter column carbs drop default, alter column fat drop default, alter column free_sugar drop default,
  alter column cholesterol drop default;
alter table public.foods
  alter column carbs drop not null, alter column fat drop not null,
  alter column free_sugar drop not null, alter column cholesterol drop not null;

create unique index if not exists uq_foods_food_key on public.foods (food_key) where food_key is not null;
create index if not exists idx_foods_validated on public.foods (id) where validated;

alter table public.foods drop constraint if exists foods_animal_source_check;
alter table public.foods add constraint foods_animal_source_check
  check (animal_source is null or animal_source in ('dairy', 'egg', 'fish', 'shellfish', 'meat', 'poultry'));
alter table public.foods drop constraint if exists foods_validated_requires_source;
alter table public.foods add constraint foods_validated_requires_source
  check (not validated or (fdc_id is not null and data_source is not null and portion_g > 0 and category_key is not null));

comment on column public.foods.validated is
  'true = aliment din catalogul validat (valori USDA la 100 g, porție realistă); doar acestea sunt recomandate.';
comment on column public.foods.food_key is 'Cheie stabilă din backend/data/food_catalog_spec.py (NULL pentru catalogul vechi).';
comment on column public.foods.fdc_id is 'ID USDA FoodData Central din care provin valorile la 100 g.';
comment on column public.foods.data_source is 'Sursa valorilor (ex. usda_sr_legacy_2018).';
comment on column public.foods.category_key is 'Categoria stabilă (nuts, seeds, legumes, ...), folosită la diversitate și alternative.';
comment on column public.foods.portion_g is 'Porția realistă în grame (ml pentru băuturi).';
comment on column public.foods.animal_source is 'Originea animală (dairy, egg, fish, shellfish, meat, poultry) sau NULL; filtrul de dietă.';
comment on column public.foods.allergen_codes is 'Coduri de alergeni (aceleași ca users.allergies).';
comment on column public.foods.flags is 'Marcaje: raw_animal, high_mercury, liver, soft_mould_cheese, high_oxalate, ultra_processed, refined_grain, added_sugar, us_enriched.';
comment on column public.foods.sodium is 'Sodiu, mg / 100 g.';
comment on column public.foods.phosphorus is 'Fosfor, mg / 100 g.';
comment on column public.foods.sugars is 'Zaharuri totale, g / 100 g.';
comment on column public.foods.alcohol is 'Alcool, g / 100 g.';
comment on table public.foods is
  'Catalog alimente. Rândurile cu validated = true au valori la 100 g din USDA FoodData Central (NULL = necunoscut).';

commit;
