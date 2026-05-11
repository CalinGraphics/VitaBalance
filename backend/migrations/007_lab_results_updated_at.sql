-- Ultima modificare a analizelor — esențial pentru invalidare recomandări (created_at rămâne la prima salvare).
ALTER TABLE public.lab_results ADD COLUMN IF NOT EXISTS updated_at timestamptz;

UPDATE public.lab_results
SET updated_at = COALESCE(created_at, now())
WHERE updated_at IS NULL;

ALTER TABLE public.lab_results ALTER COLUMN updated_at SET DEFAULT now();
ALTER TABLE public.lab_results ALTER COLUMN updated_at SET NOT NULL;

CREATE OR REPLACE FUNCTION public.lab_results_touch_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $f$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$f$;

DROP TRIGGER IF EXISTS trg_lab_results_touch_updated_at ON public.lab_results;
CREATE TRIGGER trg_lab_results_touch_updated_at
BEFORE UPDATE ON public.lab_results
FOR EACH ROW
EXECUTE FUNCTION public.lab_results_touch_updated_at();

COMMENT ON COLUMN public.lab_results.updated_at IS
  'Marcaj ultimă modificare a rândului. La update valorile biomarkerilor, created_at poate rămâne vechi — folosiți GREATEST(created_at, updated_at) pentru „prospățime” vs recomandări.';
