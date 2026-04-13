-- =============================================================================
-- Șterge datele introduse de seed_15_qa_accounts.sql (conturi testN@…).
-- Rulezi în SQL Editor Supabase / psql. Ordinea respectă FK-urile.
-- Opțional: elimină și vechile seed-uri *@vb.test dacă mai există.
-- =============================================================================

BEGIN;

DELETE FROM public.feedback
WHERE user_id IN (
  SELECT id FROM public.users
  WHERE email ~ '^test[0-9]+@vitabalance\.ro$'
     OR email LIKE '%@vb.test'
);

DELETE FROM public.recommendations
WHERE user_id IN (
  SELECT id FROM public.users
  WHERE email ~ '^test[0-9]+@vitabalance\.ro$'
     OR email LIKE '%@vb.test'
);

DELETE FROM public.lab_results
WHERE user_id IN (
  SELECT id FROM public.users
  WHERE email ~ '^test[0-9]+@vitabalance\.ro$'
     OR email LIKE '%@vb.test'
);

DELETE FROM public.users
WHERE email ~ '^test[0-9]+@vitabalance\.ro$'
   OR email LIKE '%@vb.test';

COMMIT;
