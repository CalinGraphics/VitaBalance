-- Rulare în Supabase SQL Editor (sau migrare orchestrată).
-- Integritate feedback + coloană lab_results.vitamin_c aliniată la backend/frontend.

-- Analize: acid ascorbic plasmatic (μmol/L), dacă laboratorul îl raportează
ALTER TABLE public.lab_results ADD COLUMN IF NOT EXISTS vitamin_c double precision;
COMMENT ON COLUMN public.lab_results.vitamin_c IS 'Acid ascorbic plasmatic (μmol/L), dacă este raportat de laborator.';

-- Feedback: fără rânduri orfane; recomandare obligatorie; ștergere în cascadă la ștergere recomandare
DELETE FROM public.feedback WHERE recommendation_id IS NULL;

ALTER TABLE public.feedback DROP CONSTRAINT IF EXISTS feedback_recommendation_id_fkey;
ALTER TABLE public.feedback ALTER COLUMN recommendation_id SET NOT NULL;
ALTER TABLE public.feedback
  ADD CONSTRAINT feedback_recommendation_id_fkey
  FOREIGN KEY (recommendation_id) REFERENCES public.recommendations(id) ON DELETE CASCADE;

CREATE UNIQUE INDEX IF NOT EXISTS uq_feedback_user_recommendation ON public.feedback (user_id, recommendation_id);

ALTER TABLE public.feedback DROP CONSTRAINT IF EXISTS feedback_rating_check;
ALTER TABLE public.feedback
  ADD CONSTRAINT feedback_rating_check CHECK (rating >= -1 AND rating <= 5);

ALTER TABLE public.magic_links DROP COLUMN IF EXISTS full_name;
