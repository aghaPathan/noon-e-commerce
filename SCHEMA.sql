-- Noon-E-Commerce ClickHouse Schema
-- Database: noon_intelligence

CREATE DATABASE IF NOT EXISTS noon_intelligence;

-- ============================================
-- PRODUCTS TABLE (Master data)
-- ============================================
CREATE TABLE IF NOT EXISTS noon_intelligence.products (
    sku String,
    name String,
    category String,
    brand String,
    url String,
    active UInt8 DEFAULT 1,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY sku
SETTINGS index_granularity = 8192;

-- ============================================
-- COMPETITORS TABLE (Seller/merchant data)
-- ============================================
CREATE TABLE IF NOT EXISTS noon_intelligence.competitors (
    seller_id String,
    seller_name String,
    seller_rating Nullable(Float32),
    is_noon_express UInt8 DEFAULT 0,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY seller_id
SETTINGS index_granularity = 8192;

-- ============================================
-- PRICE_HISTORY TABLE (Time-series data)
-- ============================================
CREATE TABLE IF NOT EXISTS noon_intelligence.price_history (
    sku String,
    seller_id String,
    price Float32,
    original_price Nullable(Float32),
    discount_pct Nullable(Float32),
    currency String DEFAULT 'SAR',
    in_stock UInt8,
    scraped_at DateTime,
    date Date MATERIALIZED toDate(scraped_at)
) ENGINE = ReplacingMergeTree(scraped_at)
PARTITION BY toYYYYMM(date)
ORDER BY (sku, seller_id, date)
TTL date + INTERVAL 30 DAY
SETTINGS index_granularity = 8192;

-- ============================================
-- MATERIALIZED VIEWS
-- ============================================

-- Latest price per SKU (for quick lookups)
CREATE MATERIALIZED VIEW IF NOT EXISTS noon_intelligence.mv_latest_prices
ENGINE = ReplacingMergeTree(scraped_at)
ORDER BY (sku, seller_id)
AS SELECT
    sku,
    seller_id,
    price,
    original_price,
    discount_pct,
    in_stock,
    scraped_at
FROM noon_intelligence.price_history;

-- Daily price aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS noon_intelligence.mv_daily_stats
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (sku, date)
AS SELECT
    sku,
    date,
    min(price) AS min_price,
    max(price) AS max_price,
    avg(price) AS avg_price,
    count() AS seller_count
FROM noon_intelligence.price_history
GROUP BY sku, date;

-- ============================================
-- INDEXES
-- ============================================

-- Bloom filter for text search on product names
ALTER TABLE noon_intelligence.products 
ADD INDEX idx_name_bloom name TYPE bloom_filter(0.01) GRANULARITY 1;

-- ============================================
-- SAMPLE QUERIES
-- ============================================

-- Get price history for a SKU (last 30 days)
-- SELECT * FROM noon_intelligence.price_history 
-- WHERE sku = 'N12345678' 
-- ORDER BY date DESC;

-- Get price changes (day-over-day)
-- SELECT 
--     sku,
--     date,
--     price,
--     lagInFrame(price, 1) OVER (PARTITION BY sku ORDER BY date) AS prev_price,
--     price - lagInFrame(price, 1) OVER (PARTITION BY sku ORDER BY date) AS price_change
-- FROM noon_intelligence.price_history
-- WHERE sku = 'N12345678';

-- Get lowest price seller for a SKU
-- SELECT * FROM noon_intelligence.mv_latest_prices
-- WHERE sku = 'N12345678'
-- ORDER BY price ASC
-- LIMIT 1;
