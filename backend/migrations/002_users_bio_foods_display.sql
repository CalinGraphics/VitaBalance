-- Rulare în Supabase SQL Editor — doar coloană profil.
-- (Completări vechi pentru image_url / text „nedeclarat” au fost retrase; vezi `003_schema_cleanup_rls.sql`.)

ALTER TABLE public.users ADD COLUMN IF NOT EXISTS bio text;
COMMENT ON COLUMN public.users.bio IS 'Text opțional profil / notițe utilizator.';
