-- Obiectiv caloric zilnic (kcal), opțional și strict informativ.
-- Nu este citit de motorul de recomandare; se afișează doar ca bară de progres pe dashboard.
-- Idempotent: poate fi rulat de mai multe ori.

alter table public.users
  add column if not exists caloric_goal numeric;

-- Aceleași limite ca în backend/schemas.py (500 – 10000 kcal); NULL = nesetat.
do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'users_caloric_goal_range' and conrelid = 'public.users'::regclass
  ) then
    alter table public.users
      add constraint users_caloric_goal_range
      check (caloric_goal is null or (caloric_goal >= 500 and caloric_goal <= 10000));
  end if;
end $$;

comment on column public.users.caloric_goal is
  'Obiectiv caloric zilnic (kcal), opțional; informativ, nu influențează recomandările.';
