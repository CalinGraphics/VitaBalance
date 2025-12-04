-- Seed Data pentru Foods
-- Date adaptate din baze de date publice (USDA)

-- Legume verzi (bogate în fier)
INSERT INTO foods (name, category, iron, calcium, vitamin_d, vitamin_b12, magnesium, protein, zinc, vitamin_c, fiber, calories, allergens) VALUES
('Spanac proaspăt', 'legume', 2.7, 99, 0, 0, 79, 2.9, 0.53, 28.1, 2.2, 23, NULL),
('Linte fiartă', 'leguminoase', 3.3, 19, 0, 0, 36, 9.0, 1.27, 1.5, 7.9, 116, NULL),
('Fasole neagră', 'leguminoase', 2.1, 27, 0, 0, 70, 8.9, 1.12, 0, 8.7, 132, NULL),
('Broccoli', 'legume', 0.73, 47, 0, 0, 21, 2.8, 0.41, 89.2, 2.6, 34, NULL);

-- Carne (bogată în fier heme)
INSERT INTO foods (name, category, iron, calcium, vitamin_d, vitamin_b12, magnesium, protein, zinc, vitamin_c, fiber, calories, allergens) VALUES
('Ficat de vită', 'carne', 6.5, 5, 49, 59.3, 18, 20.4, 4.9, 1.1, 0, 135, NULL),
('Carne de vită', 'carne', 2.6, 18, 7, 2.0, 20, 26.0, 6.3, 0, 0, 250, NULL),
('Carne de porc', 'carne', 0.9, 19, 13, 0.7, 22, 27.3, 2.9, 0, 0, 242, NULL),
('Piept de pui', 'carne', 0.7, 15, 5, 0.3, 25, 31.0, 0.9, 0, 0, 165, NULL);

-- Pește
INSERT INTO foods (name, category, iron, calcium, vitamin_d, vitamin_b12, magnesium, protein, zinc, vitamin_c, fiber, calories, allergens) VALUES
('Somon', 'peste', 0.8, 12, 988, 3.2, 30, 25.4, 0.6, 0, 0, 208, 'peste'),
('Ton', 'peste', 1.0, 10, 227, 2.2, 50, 30.0, 0.9, 0, 0, 144, 'peste'),
('Sardine', 'peste', 2.9, 382, 193, 8.9, 39, 24.6, 1.3, 0, 0, 208, 'peste');

-- Lactate
INSERT INTO foods (name, category, iron, calcium, vitamin_d, vitamin_b12, magnesium, protein, zinc, vitamin_c, fiber, calories, allergens) VALUES
('Lapte', 'lactate', 0.03, 113, 40, 0.4, 10, 3.4, 0.4, 0, 0, 61, 'lactoza'),
('Iaurt grecesc', 'lactate', 0.04, 110, 0, 0.4, 11, 10.0, 0.5, 0, 0, 59, 'lactoza'),
('Brânză caș', 'lactate', 0.1, 83, 0, 0.2, 8, 11.0, 0.4, 0, 0, 98, 'lactoza');

-- Cereale și semințe
INSERT INTO foods (name, category, iron, calcium, vitamin_d, vitamin_b12, magnesium, protein, zinc, vitamin_c, fiber, calories, allergens) VALUES
('Semințe de dovleac', 'seminte', 3.3, 46, 0, 0, 262, 18.6, 6.6, 0.3, 6.0, 446, NULL),
('Semințe de chia', 'seminte', 7.7, 631, 0, 0, 335, 16.5, 4.6, 1.6, 34.4, 486, NULL),
('Almonds', 'nuci', 3.7, 269, 0, 0, 270, 21.2, 3.1, 0, 12.5, 579, 'nuci'),
('Ovăz', 'cereale', 4.7, 54, 0, 0, 177, 16.9, 3.97, 0, 10.6, 389, 'gluten');

-- Alimente fortificate
INSERT INTO foods (name, category, iron, calcium, vitamin_d, vitamin_b12, magnesium, protein, zinc, vitamin_c, fiber, calories, allergens) VALUES
('Lapte fortificat cu vitamina D', 'lactate', 0.03, 113, 120, 0.4, 10, 3.4, 0.4, 0, 0, 61, 'lactoza'),
('Cereale fortificate', 'cereale', 18.0, 1000, 100, 6.0, 100, 10.0, 15.0, 0, 10.0, 379, 'gluten');