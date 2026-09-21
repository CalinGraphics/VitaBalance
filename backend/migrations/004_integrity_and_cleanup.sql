-- Integritate date + curățenie indexuri. Idempotent: poate fi rulat de mai multe ori.

-- 1) Corectare dată: înălțime introdusă în metri (ex. 1.76) în loc de cm. Aplicăm doar valorilor clar în metri.
update public.users set height = round((height * 100)::numeric, 1)::double precision
where height > 0 and height < 3;

-- 2) Constrângeri de domeniu pe profil (aceleași valori ca în formularul din frontend și în schemas.UserCreate).
--    Coloanele rămân nullable (conturi create înainte de completarea profilului).
alter table public.users drop constraint if exists users_sex_check;
alter table public.users add constraint users_sex_check
  check (sex is null or sex in ('F', 'M', 'other'));

alter table public.users drop constraint if exists users_activity_level_check;
alter table public.users add constraint users_activity_level_check
  check (activity_level is null or activity_level in ('sedentary', 'moderate', 'active', 'very_active'));

alter table public.users drop constraint if exists users_diet_type_check;
alter table public.users add constraint users_diet_type_check
  check (diet_type is null or diet_type in ('omnivore', 'vegetarian', 'vegan', 'pescatarian'));

alter table public.users drop constraint if exists users_body_metrics_range;
alter table public.users add constraint users_body_metrics_range
  check (
    (age is null or age between 1 and 120)
    and (weight is null or weight between 20 and 400)
    and (height is null or height between 50 and 260)
  );

-- 3) Indexuri redundante (acoperite de alte indexuri; scad viteza scrierilor fără niciun câștig la citire)
drop index if exists public.idx_users_email;                    -- dublează users_email_key / users_email_lower_key
drop index if exists public.idx_feedback_user_recommendation;   -- dublează uq_feedback_user_recommendation
drop index if exists public.idx_feedback_user_id;               -- prefix al idx_feedback_user_food / uq_feedback_user_recommendation
drop index if exists public.idx_recommendations_user_id;        -- prefix al idx_recommendations_user_created

-- 4) Constrângere CHECK duplicată pe feedback.rating (identică cu feedback_rating_check)
alter table public.feedback drop constraint if exists feedback_rating_range;

-- 5) Aliment duplicat: "Kombucha" id 387 (60 kcal, 14 g carbohidrați) e dublul lui id 211 (30 kcal, 7 g) — valori per
--    porție din lotul 380+, nu per 100 g. Se șterge doar dacă nu e referit de nicio recomandare.
delete from public.foods f
 where f.id = 387 and f.name = 'Kombucha'
   and not exists (select 1 from public.recommendations r where r.food_id = f.id);
