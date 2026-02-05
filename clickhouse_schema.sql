-- Noon E-Commerce ClickHouse Schema
-- Database: noon_intelligence
-- Purpose: Time-series price history analytics

-- ============================================
-- PRODUCTS TABLE (Reference data)
-- ============================================
CREATE TABLE IF NOT EXISTS products (
    sku String,
    name String,
    category Nullable(String),
    brand Nullable(String),
    url Nullable(String),
    active UInt8 DEFAULT 1,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY sku;

-- ============================================
-- COMPETITORS TABLE (Seller reference)
-- ============================================
CREATE TABLE IF NOT EXISTS competitors (
    seller_id String,
    seller_name String,
    seller_url Nullable(String),
    is_noon UInt8 DEFAULT 0,
    created_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(created_at)
ORDER BY seller_id;

-- ============================================
-- PRICE HISTORY TABLE (Core time-series data)
-- ============================================
CREATE TABLE IF NOT EXISTS price_history (
    sku String,
    seller_id String DEFAULT 'noon',
    price Float64,
    original_price Nullable(Float64),
    discount_pct Nullable(Float64),
    currency String DEFAULT 'SAR',
    in_stock UInt8 DEFAULT 1,
    scraped_at DateTime DEFAULT now(),
    
    -- Partition by month for efficient queries
    INDEX idx_sku sku TYPE bloom_filter GRANULARITY 3,
    INDEX idx_date scraped_at TYPE minmax GRANULARITY 1
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(scraped_at)
ORDER BY (sku, seller_id, scraped_at)
TTL scraped_at + INTERVAL 2 YEAR;

-- ============================================
-- MATERIALIZED VIEW: Latest Prices
-- ============================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_latest_prices
ENGINE = ReplacingMergeTree(scraped_at)
ORDER BY (sku, seller_id)
AS SELECT
    sku,
    seller_id,
    price,
    original_price,
    discount_pct,
    currency,
    in_stock,
    scraped_at
FROM price_history;

-- ============================================
-- ALERTS TABLE (Price change alerts)
-- ============================================
CREATE TABLE IF NOT EXISTS alerts (
    id UUID DEFAULT generateUUIDv4(),
    sku String,
    seller_id String,
    alert_type String,  -- 'price_drop', 'price_increase', 'stock_change'
    previous_value Float64,
    current_value Float64,
    change_pct Float64,
    acknowledged UInt8 DEFAULT 0,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (created_at, sku)
TTL created_at + INTERVAL 90 DAY;

-- ============================================
-- SAMPLE DATA (for testing)
-- ============================================
-- Insert a test product
INSERT INTO products (sku, name, category, brand) VALUES
    ('N12345678', 'Test Product', 'Electronics', 'TestBrand');

-- Insert noon as default competitor
INSERT INTO competitors (seller_id, seller_name, is_noon) VALUES
    ('noon', 'Noon', 1);
