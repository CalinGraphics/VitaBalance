-- =============================================================================
-- VitaBalance – 15 conturi fictive (nume romanesti) pentru test recomandari
-- =============================================================================
-- Email: test1@vitabalance.ro … test15@vitabalance.ro
-- Parola (toate): VitaTest15!
--
-- Legenda persona: vezi conturi_fictive.txt din acelasi folder.
-- Stergere: rulezi delete_15_qa_accounts.sql inainte de re-import, daca e cazul.
--
-- Alergiile folosesc valorile din UI (frontend/src/shared/constants/allergies.ts).
-- Conditiile medicale folosesc valorile din medicalConditions.ts (coduri, nu etichete).
-- Observatiile din analize (notes) se imbina in profilul efectiv la recomandari –
-- vezi RecommenderService.generate_recommendations + DeficitCalculator (valori lab).
-- =============================================================================

BEGIN;

DELETE FROM public.feedback
WHERE user_id IN (
  SELECT id FROM public.users
  WHERE email ~ '^test[0-9]+@vitabalance\.ro$' OR email LIKE '%@vb.test'
);

DELETE FROM public.recommendations
WHERE user_id IN (
  SELECT id FROM public.users
  WHERE email ~ '^test[0-9]+@vitabalance\.ro$' OR email LIKE '%@vb.test'
);

DELETE FROM public.lab_results
WHERE user_id IN (
  SELECT id FROM public.users
  WHERE email ~ '^test[0-9]+@vitabalance\.ro$' OR email LIKE '%@vb.test'
);

DELETE FROM public.users
WHERE email ~ '^test[0-9]+@vitabalance\.ro$' OR email LIKE '%@vb.test';

INSERT INTO public.users (
  email, password_hash, name, age, sex, weight, height,
  activity_level, diet_type, allergies, medical_conditions
) VALUES
  ('test1@vitabalance.ro', '$2b$12$blqkfMN72vpPKRKB0THjCO5V4qrX7qwC9.HMzsga8bk7FNcOYHJ/W', 'Andrei Popescu', 34, 'M', 79, 182, 'moderate', 'omnivore', 'nuci, arahide', 'colesterol_ridicat'),
  ('test2@vitabalance.ro', '$2b$12$blqkfMN72vpPKRKB0THjCO5V4qrX7qwC9.HMzsga8bk7FNcOYHJ/W', 'Maria Ionescu', 29, 'F', 56, 162, 'moderate', 'omnivore', 'oua', 'anemie'),
  ('test3@vitabalance.ro', '$2b$12$blqkfMN72vpPKRKB0THjCO5V4qrX7qwC9.HMzsga8bk7FNcOYHJ/W', 'Radu Dumitrescu', 42, 'M', 84, 178, 'sedentary', 'omnivore', 'peste', ''),
  ('test4@vitabalance.ro', '$2b$12$blqkfMN72vpPKRKB0THjCO5V4qrX7qwC9.HMzsga8bk7FNcOYHJ/W', 'Elena Vasilescu', 27, 'F', 53, 164, 'active', 'vegan', 'soia', 'deficienta_b12, deficienta_vitamin_d'),
  ('test5@vitabalance.ro', '$2b$12$blqkfMN72vpPKRKB0THjCO5V4qrX7qwC9.HMzsga8bk7FNcOYHJ/W', 'Victoria Munteanu', 69, 'F', 71, 158, 'sedentary', 'omnivore', '', 'osteoporoza, deficienta_vitamin_d'),
  ('test6@vitabalance.ro', '$2b$12$blqkfMN72vpPKRKB0THjCO5V4qrX7qwC9.HMzsga8bk7FNcOYHJ/W', 'Cristian Moldovan', 26, 'M', 90, 188, 'very_active', 'omnivore', 'crustacee', 'obezitate'),
  ('test7@vitabalance.ro', '$2b$12$blqkfMN72vpPKRKB0THjCO5V4qrX7qwC9.HMzsga8bk7FNcOYHJ/W', 'Ana Stancu', 36, 'F', 64, 168, 'moderate', 'pescatarian', 'sesam', 'tiroida'),
  ('test8@vitabalance.ro', '$2b$12$blqkfMN72vpPKRKB0THjCO5V4qrX7qwC9.HMzsga8bk7FNcOYHJ/W', 'Mihai Radu', 46, 'M', 86, 176, 'moderate', 'omnivore', 'lactoza', ''),
  ('test9@vitabalance.ro', '$2b$12$blqkfMN72vpPKRKB0THjCO5V4qrX7qwC9.HMzsga8bk7FNcOYHJ/W', 'Gabriela Stan', 31, 'F', 59, 166, 'moderate', 'omnivore', 'gluten', 'celiachie'),
  ('test10@vitabalance.ro', '$2b$12$blqkfMN72vpPKRKB0THjCO5V4qrX7qwC9.HMzsga8bk7FNcOYHJ/W', 'Florin Georgescu', 53, 'M', 98, 174, 'sedentary', 'omnivore', 'mustar', 'hipertensiune, reflux'),
  ('test11@vitabalance.ro', '$2b$12$blqkfMN72vpPKRKB0THjCO5V4qrX7qwC9.HMzsga8bk7FNcOYHJ/W', 'Doina Constantinescu', 57, 'F', 78, 160, 'sedentary', 'omnivore', 'arahide', 'diabet'),
  ('test12@vitabalance.ro', '$2b$12$blqkfMN72vpPKRKB0THjCO5V4qrX7qwC9.HMzsga8bk7FNcOYHJ/W', 'Vasile Toma', 61, 'M', 81, 170, 'sedentary', 'omnivore', '', 'insuficienta_renala'),
  ('test13@vitabalance.ro', '$2b$12$blqkfMN72vpPKRKB0THjCO5V4qrX7qwC9.HMzsga8bk7FNcOYHJ/W', 'Laura Enache', 39, 'F', 63, 165, 'moderate', 'omnivore', 'peste', 'reflux'),
  ('test14@vitabalance.ro', '$2b$12$blqkfMN72vpPKRKB0THjCO5V4qrX7qwC9.HMzsga8bk7FNcOYHJ/W', 'Paul Simion', 48, 'M', 88, 180, 'moderate', 'omnivore', 'nuci, sesam', 'deficienta_vitamin_d'),
  ('test15@vitabalance.ro', '$2b$12$blqkfMN72vpPKRKB0THjCO5V4qrX7qwC9.HMzsga8bk7FNcOYHJ/W', 'Roxana Petrescu', 23, 'F', 52, 163, 'active', 'vegetarian', 'oua', 'anemie');

INSERT INTO public.lab_results (
  user_id, hemoglobin, ferritin, vitamin_d, vitamin_b12, calcium, magnesium,
  zinc, protein, folate, vitamin_a, iodine, vitamin_k, potassium, notes
)
SELECT
  u.id,
  v.hemoglobin,
  v.ferritin,
  v.vitamin_d,
  v.vitamin_b12,
  v.calcium,
  v.magnesium,
  v.zinc,
  v.protein,
  v.folate,
  v.vitamin_a,
  v.iodine,
  v.vitamin_k,
  v.potassium,
  v.notes
FROM (VALUES
  ('test1@vitabalance.ro'::text, 14.2::double precision, 48.0::double precision, 38.0::double precision, 420.0::double precision, 9.3::double precision, 2.05::double precision, 92.0::double precision, 6.9::double precision, 8.2::double precision, 46.0::double precision, 125.0::double precision, 1.15::double precision, 4.25::double precision, 'Hemoleucograma si profil metabolic – fara anomalii semnificative.'::text),
  ('test2@vitabalance.ro', 11.6, 11.0, 26.0, 340.0, 9.0, 1.88, 78.0, 6.45, 4.8, 38.0, 108.0, 0.95, 4.0, 'Ferritina scazuta, recomandat supliment fier sub supraveghere medicala.'),
  ('test3@vitabalance.ro', 11.2, NULL, 29.0, 375.0, 9.05, 1.92, 84.0, 6.55, 6.0, 41.0, 114.0, 1.08, 4.05, 'Hemoglobina scazuta; ferritina necompletata in buletin.'),
  ('test4@vitabalance.ro', 12.4, 32.0, 24.0, 165.0, 8.95, 1.82, 74.0, 6.35, 7.2, 37.0, 98.0, 1.0, 3.85, 'Regim vegan; B12 sub prag, urmarire cu medicul curant.'),
  ('test5@vitabalance.ro', 12.8, 35.0, 14.0, 265.0, 8.1, 1.72, 76.0, 6.25, 5.2, 33.0, 102.0, 0.88, 3.75, 'Osteoporoza cunoscuta; vitamina D si calciu sub tinta terapeutica.'),
  ('test6@vitabalance.ro', 15.2, 52.0, 34.0, 430.0, 9.35, 2.08, 96.0, 5.1, 8.8, 49.0, 128.0, 1.22, 4.35, 'Antrenament zilnic; proteine serice sub prag – evaluat cu nutritionist.'),
  ('test7@vitabalance.ro', 13.1, 36.0, 28.5, 355.0, 9.08, 1.89, 52.0, 6.65, 6.1, 40.5, 111.0, 1.02, 4.02, 'Zinc seric scazut; dieta pescatariana.'),
  ('test8@vitabalance.ro', 14.3, 58.0, 27.0, 400.0, 8.25, 1.86, 81.0, 6.58, 6.0, 39.5, 117.0, 1.09, 4.0, 'Calciu ionic scazut; intoleranta la lactoza – surse alternative de calciu.'),
  ('test9@vitabalance.ro', 13.4, 41.0, 30.5, 405.0, 9.18, 1.94, 87.0, 6.68, 6.4, 41.5, 118.0, 1.1, 4.08, 'Boala celiaca stabilizata; profil orientativ in limite.'),
  ('test10@vitabalance.ro', 14.0, 46.0, 28.0, 405.0, 9.12, 1.97, 85.0, 6.62, 6.35, 42.5, 118.5, 1.07, 4.06, 'HTA si reflux – control metabolic de rutina.'),
  ('test11@vitabalance.ro', 12.9, 43.0, 26.5, 388.0, 9.0, 1.9, 83.0, 6.58, 6.2, 40.8, 116.5, 1.05, 4.04, 'HbA1c urmarita in ambulator; profil lipido-glucidic in evaluare.'),
  ('test12@vitabalance.ro', 13.6, 45.0, 25.5, 380.0, 8.98, 1.88, 82.0, 6.48, 6.0, 39.8, 115.0, 1.04, 4.18, 'Boala cronica de rinichi stadiu stabil; potasiu in limite stranse.'),
  ('test13@vitabalance.ro', 12.7, 34.0, 29.5, 370.0, 8.98, 1.91, 80.0, 6.52, 6.15, 40.8, 116.0, 1.06, 4.05, 'Nu mananc peste, pui, porc. Evit cafea. Restrictii consemnate in observatie (se imbina cu conditiile din profil la generarea recomandarilor).'),
  ('test14@vitabalance.ro', NULL::double precision, NULL::double precision, NULL::double precision, NULL::double precision, NULL::double precision, NULL::double precision, NULL::double precision, NULL::double precision, NULL::double precision, NULL::double precision, NULL::double precision, NULL::double precision, NULL::double precision, 'Pacientul raporteaza oboseala; medic curant noteaza deficit de vitamina D si magneziu – analize numerice inca necompletate in sistem.'),
  ('test15@vitabalance.ro', 11.9, 18.0, 25.0, 305.0, 8.88, 1.83, 70.0, 6.38, 6.6, 38.5, 106.0, 0.98, 3.92, 'Vegetariana; ferritina scazuta, suspiciune anemie feripriva.')
) AS v(email, hemoglobin, ferritin, vitamin_d, vitamin_b12, calcium, magnesium, zinc, protein, folate, vitamin_a, iodine, vitamin_k, potassium, notes)
JOIN public.users u ON u.email = v.email;

COMMIT;
