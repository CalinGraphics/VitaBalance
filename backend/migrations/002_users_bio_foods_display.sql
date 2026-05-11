-- Rulare în Supabase SQL Editor (sau prin MCP apply_migration) — idempotent acolo unde e posibil.
-- 1) Coloană lipsă pentru API (auth/me, magic link).
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS bio text;
COMMENT ON COLUMN public.users.bio IS 'Text opțional profil / notițe utilizator.';

-- 2) Completare câmpuri afișare catalog: alergeni necompletați + placeholder imagine stabil (per rând).
--    „nedeclarat” = sursa CSV nu conținea alergeni; utilizatorul trebuie să verifice eticheta.
UPDATE public.foods
SET
  allergens = COALESCE(NULLIF(TRIM(allergens), ''), 'nedeclarat'),
  image_url = CASE
    WHEN image_url IS NULL OR BTRIM(image_url) = '' THEN
      'https://picsum.photos/seed/vb-' || md5(name || id::text) || '/512/512'
    ELSE image_url
  END
WHERE allergens IS NULL
   OR TRIM(COALESCE(allergens, '')) = ''
   OR image_url IS NULL
   OR BTRIM(COALESCE(image_url, '')) = '';
