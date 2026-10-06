-- 013: indexuri pentru interogările făcute la fiecare încărcare a paginii de recomandări. Idempotent.
--
-- recommendations: citite după user_id, ordonate după scor (RecommendationRepository.get_by_user_id). Indexul vechi
-- (user_id, created_at desc) rămâne pentru get_first_by_user_id.
create index if not exists idx_recommendations_user_score on public.recommendations (user_id, score desc, id);
-- lab_results: ultimul rând al utilizatorului, ordonat după updated_at, created_at (get_latest_by_user_id).
create index if not exists idx_lab_results_user_latest on public.lab_results (user_id, updated_at desc, created_at desc);
-- idx_lab_results_user_id devine redundant (prefixul noului index).
drop index if exists public.idx_lab_results_user_id;
-- feedback: get_by_user_id e acoperit de uq_feedback_user_food (user_id, food_id) — nu e nevoie de alt index.
