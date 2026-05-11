-- Curățenie schema + RLS. Backend-ul VitaBalance folosește SUPABASE_KEY = service_role (bypass RLS).
-- Nu rula din browser cu cheie anon fără politici RLS suplimentare.

DROP VIEW IF EXISTS public.feedback_view CASCADE;
DROP VIEW IF EXISTS public.lab_results_view CASCADE;
DROP VIEW IF EXISTS public.magic_links_view CASCADE;
DROP VIEW IF EXISTS public.recommendations_view CASCADE;
DROP VIEW IF EXISTS public.user_profiles_view CASCADE;
DROP VIEW IF EXISTS public.users_clean_view CASCADE;

ALTER TABLE public.feedback DROP COLUMN IF EXISTS comment;
ALTER TABLE public.feedback DROP COLUMN IF EXISTS tried;
ALTER TABLE public.feedback DROP COLUMN IF EXISTS worked;

UPDATE public.foods SET allergens = NULL WHERE trim(coalesce(allergens, '')) IN ('nedeclarat', '');

ALTER TABLE public.foods DROP COLUMN IF EXISTS image_url;

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.foods ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lab_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.magic_links ENABLE ROW LEVEL SECURITY;
