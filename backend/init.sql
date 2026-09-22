-- SellerAI: Бастапқы деректер қорының сұлбасы (PostgreSQL Schema)

-- 1. Қолданушылар кестесі (Users)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    email VARCHAR(255) UNIQUE,
    full_name VARCHAR(255),
    tariff_plan VARCHAR(50) NOT NULL DEFAULT 'free',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Қадағаланатын тауарлар кестесі (Products)
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_url TEXT NOT NULL,
    marketplace VARCHAR(50) NOT NULL DEFAULT 'kaspi', -- 'kaspi', 'wildberries', т.б.
    sku VARCHAR(100),
    product_name VARCHAR(255),
    cost_price DECIMAL(10, 2), -- Селлердің өзіндік құны (маржа есептеуге)
    current_price DECIMAL(10, 2), -- Селлердің ағымдағы сату бағасы
    min_price_threshold DECIMAL(10, 2), -- Минималды баға шегі (демпингтен сақтану)
    monitoring_interval_hours INT NOT NULL DEFAULT 6,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_checked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Баға тарихы мен бәсекелестер кестесі (Price History)
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    seller_name VARCHAR(255) NOT NULL, -- Бәсекелестің немесе селлердің өзінің дүкен атауы
    is_my_shop BOOLEAN NOT NULL DEFAULT FALSE,
    price DECIMAL(10, 2) NOT NULL,
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    delivery_type VARCHAR(100), -- 'Express', 'Standard', 'Postomat', т.б.
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. AI Ұсыныстары мен ескертулер тарихы (AI Insights / Alerts)
CREATE TABLE IF NOT EXISTS ai_recommendations (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    recommended_price DECIMAL(10, 2),
    alert_type VARCHAR(50) NOT NULL, -- 'DUMPING_DETECTED', 'PRICE_DROP', 'OPPORTUNITY'
    analysis_text TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индекстер (Performance Optimization)
CREATE INDEX IF NOT EXISTS idx_products_user_id ON products(user_id);
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_price_history_product_id ON price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_price_history_recorded_at ON price_history(recorded_at);
CREATE INDEX IF NOT EXISTS idx_ai_recommendations_product_id ON ai_recommendations(product_id);
