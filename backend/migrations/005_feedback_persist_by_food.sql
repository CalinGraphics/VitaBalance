-- Feedback persistent per (utilizator, aliment): supraviețuiește regenerării / înlocuirii recomandărilor.
-- Înainte: feedback.recommendation_id era NOT NULL cu ON DELETE CASCADE, deci ștergerea recomandării
-- (regenerare sau „înlocuiește”) ștergea și feedback-ul (dislike-ul se pierdea). Idempotent.

-- 1) food_id devine cheia reală a feedback-ului: int (ca foods.id), obligatoriu, cu FK către catalog.
update public.feedback f
   set food_id = r.food_id
  from public.recommendations r
 where f.food_id is null and r.id = f.recommendation_id;

alter table public.feedback alter column food_id type integer;
alter table public.feedback alter column food_id set not null;

alter table public.feedback drop constraint if exists feedback_food_id_fkey;
alter table public.feedback add constraint feedback_food_id_fkey
  foreign key (food_id) references public.foods (id) on delete cascade;

-- 2) recommendation_id devine opțional și se anulează (nu se șterge feedback-ul) când recomandarea dispare.
alter table public.feedback alter column recommendation_id drop not null;

alter table public.feedback drop constraint if exists feedback_recommendation_id_fkey;
alter table public.feedback add constraint feedback_recommendation_id_fkey
  foreign key (recommendation_id) references public.recommendations (id) on delete set null;

-- 3) Un singur vot per (utilizator, aliment): păstrăm cel mai recent, apoi impunem unicitatea.
delete from public.feedback f
 using public.feedback g
 where f.user_id = g.user_id and f.food_id = g.food_id and f.id < g.id;

create unique index if not exists uq_feedback_user_food on public.feedback (user_id, food_id);

-- Indexuri înlocuite de uq_feedback_user_food (prefix user_id, food_id) sau devenite inutile
drop index if exists public.uq_feedback_user_recommendation;
drop index if exists public.idx_feedback_user_recommendation;
drop index if exists public.idx_feedback_user_food;
drop index if exists public.idx_feedback_user_id;
-- idx_feedback_recommendation_id rămâne: susține FK-ul (SET NULL la ștergerea unei recomandări)
-- idx_feedback_food_id (parțial) rămâne: agregări pe aliment și FK către foods

comment on table public.feedback is
  'Apreciere (rating) a utilizatorului pentru un aliment; unică per (user_id, food_id) și persistă când recomandarea e regenerată/ștearsă.';
comment on column public.feedback.food_id is 'FK foods.id: alimentul evaluat (cheia feedback-ului).';
comment on column public.feedback.recommendation_id is
  'Recomandarea curentă asociată (opțional); devine NULL când recomandarea este ștearsă, feedback-ul rămâne.';
