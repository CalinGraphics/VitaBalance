-- VitaBalance Database Schema

-- Tabela Users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    age INTEGER,
    sex VARCHAR(10) CHECK (sex IN ('M', 'F', 'other')),
    weight FLOAT,
    height FLOAT,
    activity_level VARCHAR(20) CHECK (activity_level IN ('sedentary', 'moderate', 'active', 'very_active')),
    diet_type VARCHAR(20) CHECK (diet_type IN ('omnivore', 'vegetarian', 'vegan', 'pescatarian')),
    allergies TEXT,
    medical_conditions TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index pentru email (deja există prin UNIQUE, dar explicit pentru performanță)
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Tabela Lab Results
CREATE TABLE IF NOT EXISTS lab_results (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    hemoglobin FLOAT,
    ferritin FLOAT,
    vitamin_d FLOAT,
    vitamin_b12 FLOAT,
    calcium FLOAT,
    magnesium FLOAT,
    zinc FLOAT,
    protein FLOAT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index pentru user_id pentru query-uri rapide
CREATE INDEX IF NOT EXISTS idx_lab_results_user_id ON lab_results(user_id);
CREATE INDEX IF NOT EXISTS idx_lab_results_created_at ON lab_results(created_at DESC);

-- Tabela Foods
CREATE TABLE IF NOT EXISTS foods (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50),
    iron FLOAT DEFAULT 0,
    calcium FLOAT DEFAULT 0,
    vitamin_d FLOAT DEFAULT 0,
    vitamin_b12 FLOAT DEFAULT 0,
    magnesium FLOAT DEFAULT 0,
    protein FLOAT DEFAULT 0,
    zinc FLOAT DEFAULT 0,
    vitamin_c FLOAT DEFAULT 0,
    fiber FLOAT DEFAULT 0,
    calories FLOAT DEFAULT 0,
    allergens TEXT,
    image_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index pentru căutare rapidă după nume și categorie
CREATE INDEX IF NOT EXISTS idx_foods_name ON foods(name);
CREATE INDEX IF NOT EXISTS idx_foods_category ON foods(category);

-- Tabela Recommendations
CREATE TABLE IF NOT EXISTS recommendations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    food_id INTEGER NOT NULL REFERENCES foods(id) ON DELETE CASCADE,
    score FLOAT NOT NULL,
    explanation TEXT NOT NULL,
    portion_suggested FLOAT,
    coverage_percentage FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index pentru query-uri rapide
CREATE INDEX IF NOT EXISTS idx_recommendations_user_id ON recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_food_id ON recommendations(food_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_created_at ON recommendations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_recommendations_score ON recommendations(score DESC);

-- Tabela Feedback
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recommendation_id INTEGER REFERENCES recommendations(id) ON DELETE SET NULL,
    rating INTEGER NOT NULL CHECK (rating >= -1 AND rating <= 5),
    comment TEXT,
    tried BOOLEAN DEFAULT FALSE,
    worked BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index pentru feedback
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_recommendation_id ON feedback(recommendation_id);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback(created_at DESC);

-- Trigger pentru actualizarea automată a updated_at în users
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comentarii pentru documentație
COMMENT ON TABLE users IS 'Utilizatori ai aplicației VitaBalance';
COMMENT ON TABLE lab_results IS 'Rezultate analize de laborator pentru utilizatori';
COMMENT ON TABLE foods IS 'Baza de date cu alimente și valori nutriționale';
COMMENT ON TABLE recommendations IS 'Recomandări personalizate de alimente pentru utilizatori';
COMMENT ON TABLE feedback IS 'Feedback de la utilizatori despre recomandări';