-- Rulare în Supabase SQL Editor. Clarificări schema + aliniere la aplicația VitaBalance (magic link, un singur nume afișat).

-- ---------------------------------------------------------------------------
-- users: elimină duplicatul name / full_name (aplicația folosește doar `name`)
-- ---------------------------------------------------------------------------
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'full_name'
  ) THEN
    UPDATE public.users
    SET name = COALESCE(NULLIF(trim(name), ''), NULLIF(trim(full_name), ''), name);
    ALTER TABLE public.users DROP COLUMN full_name;
  END IF;
END $$;

-- Magic link creează utilizatori fără parolă; înregistrarea cu parolă rămâne opțională legacy
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'password_hash'
  ) THEN
    ALTER TABLE public.users ALTER COLUMN password_hash DROP NOT NULL;
  END IF;
END $$;

COMMENT ON TABLE public.users IS 'Profil utilizator: identitate (email, name), antropometrie, dietă, alergii; autentificare principală magic link.';
COMMENT ON COLUMN public.users.id IS 'Identificator unic (PK).';
COMMENT ON COLUMN public.users.email IS 'Email unic; folosit la magic link și la identificare în JWT.';
COMMENT ON COLUMN public.users.name IS 'Numele complet afișat în UI (un singur câmp; nu există coloană separată full_name).';
COMMENT ON COLUMN public.users.password_hash IS 'Opțional: bcrypt pentru fluxul legacy /register cu parolă. Conturi doar magic link → de obicei NULL.';

COMMENT ON TABLE public.lab_results IS 'Rezultate analize medicale; același utilizator poate avea mai multe rânduri (istoric / re-salvări).';
COMMENT ON COLUMN public.lab_results.id IS 'PK al acestui rând = o înregistrare salvată de analize la un moment dat.';
COMMENT ON COLUMN public.lab_results.user_id IS 'FK către users.id: a cui sunt valorile din acest rând.';

COMMENT ON TABLE public.foods IS 'Catalog nutrienți per 100 g; id este cheie stabilă (nu se „renumără” la 1..N fără migrare de FK-uri).';
COMMENT ON COLUMN public.foods.id IS 'PK surrogate: identificator stabil în catalog. Ordinea afișării se face prin sortare (categorie, nume), nu prin id.';

COMMENT ON TABLE public.recommendations IS 'Recomandări materializate: legătură user_id–food_id cu scor, acoperire și text explicativ salvat.';
COMMENT ON COLUMN public.recommendations.user_id IS 'FK users: pentru cine este recomandarea.';
COMMENT ON COLUMN public.recommendations.food_id IS 'FK foods: ce aliment este recomandat.';

COMMENT ON TABLE public.feedback IS 'Apreciere (like/dislike) pe o recomandare concretă; legat de recommendations.id.';
COMMENT ON TABLE public.magic_links IS 'Tokenuri one-time pentru autentificare fără parolă (magic link pe email).';
