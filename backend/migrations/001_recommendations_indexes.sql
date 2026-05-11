-- Rulare manuală în Supabase SQL Editor sau psql (adaptă schema dacă difere).
-- Accelerează citirile/ștergerile pe recomandări per utilizator.

CREATE INDEX IF NOT EXISTS idx_recommendations_user_id
  ON public.recommendations (user_id);

CREATE INDEX IF NOT EXISTS idx_recommendations_user_created
  ON public.recommendations (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_recommendations_food_id
  ON public.recommendations (food_id);

CREATE INDEX IF NOT EXISTS idx_feedback_user_id
  ON public.feedback (user_id);

CREATE INDEX IF NOT EXISTS idx_lab_results_user_id
  ON public.lab_results (user_id);
