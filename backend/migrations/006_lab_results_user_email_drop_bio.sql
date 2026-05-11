-- Rulare în Supabase SQL Editor (după 004 / 005 dacă le folosești).
-- 1) lab_results.user_email = email utilizatorului (după user_id logic); sincronizare automată.
-- 2) Elimină users.bio (nefolosit / redundant cu profilul medical).

-- ---------------------------------------------------------------------------
-- lab_results.user_email
-- ---------------------------------------------------------------------------
ALTER TABLE public.lab_results ADD COLUMN IF NOT EXISTS user_email text;

UPDATE public.lab_results lr
SET user_email = u.email
FROM public.users u
WHERE u.id = lr.user_id
  AND (lr.user_email IS NULL OR btrim(lr.user_email) = '');

-- Rânduri orfane (user șters) — le eliminăm ca să putem impune NOT NULL
DELETE FROM public.lab_results lr
WHERE NOT EXISTS (SELECT 1 FROM public.users u WHERE u.id = lr.user_id);

CREATE OR REPLACE FUNCTION public.lab_results_set_user_email()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $f$
BEGIN
  SELECT u.email INTO STRICT NEW.user_email
  FROM public.users u
  WHERE u.id = NEW.user_id;
  RETURN NEW;
EXCEPTION
  WHEN NO_DATA_FOUND THEN
    RAISE EXCEPTION 'lab_results: user_id % inexistent în users', NEW.user_id
      USING ERRCODE = '23503';
END;
$f$;

DROP TRIGGER IF EXISTS trg_lab_results_set_user_email ON public.lab_results;
CREATE TRIGGER trg_lab_results_set_user_email
BEFORE INSERT OR UPDATE ON public.lab_results
FOR EACH ROW
EXECUTE FUNCTION public.lab_results_set_user_email();

COMMENT ON COLUMN public.lab_results.user_email IS
  'Email utilizator (denormalizat din users), păstrat lângă user_id pentru citire rapidă în SQL/exports. Sincronizat prin trigger; la schimbare email pe users se actualizează și rândurile lab.';

-- Propagare email când utilizatorul își schimbă emailul în users
CREATE OR REPLACE FUNCTION public.users_propagate_email_to_lab_results()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $f$
BEGIN
  IF NEW.email IS DISTINCT FROM OLD.email THEN
    UPDATE public.lab_results
    SET user_email = NEW.email
    WHERE user_id = NEW.id;
  END IF;
  RETURN NEW;
END;
$f$;

DROP TRIGGER IF EXISTS trg_users_email_lab_results ON public.users;
CREATE TRIGGER trg_users_email_lab_results
AFTER UPDATE OF email ON public.users
FOR EACH ROW
EXECUTE FUNCTION public.users_propagate_email_to_lab_results();

ALTER TABLE public.lab_results ALTER COLUMN user_email SET NOT NULL;

COMMENT ON COLUMN public.lab_results.id IS
  'PK unic al acestui rând (o salvare de analize). user_id = cui îi aparțin; user_email = copie denormalizată a users.email pentru citire rapidă (nu înlocuiește id).';

-- ---------------------------------------------------------------------------
-- users: elimină bio
-- ---------------------------------------------------------------------------
ALTER TABLE public.users DROP COLUMN IF EXISTS bio;

-- Dacă CREATE TRIGGER ... EXECUTE FUNCTION e respinsă de versiunea Postgres, înlocuiește cu:
-- EXECUTE PROCEDURE public.lab_results_set_user_email();
-- EXECUTE PROCEDURE public.users_propagate_email_to_lab_results();
