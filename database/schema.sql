-- database/schema.sql
-- AlphaEdge V13.0.7 – TimescaleDB Schema
-- Item 16: TimescaleDB Integration

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================
-- OHLCV DATA TABLE
-- ============================================
CREATE TABLE ohlcv_data (
    time TIMESTAMPTZ NOT NULL,
    token TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    open DECIMAL NOT NULL,
    high DECIMAL NOT NULL,
    low DECIMAL NOT NULL,
    close DECIMAL NOT NULL,
    volume DECIMAL NOT NULL,
    source TEXT NOT NULL
);

-- Convert to hypertable (time-series)
SELECT create_hypertable('ohlcv_data', 'time');

-- Create indexes
CREATE INDEX idx_ohlcv_token_timeframe ON ohlcv_data (token, timeframe, time DESC);
CREATE INDEX idx_ohlcv_time ON ohlcv_data (time DESC);

-- ============================================
-- LIQUIDITY DATA TABLE
-- ============================================
CREATE TABLE liquidity_data (
    time TIMESTAMPTZ NOT NULL,
    token TEXT NOT NULL,
    exchange TEXT NOT NULL,
    bid_depth DECIMAL NOT NULL,
    ask_depth DECIMAL NOT NULL,
    spread DECIMAL NOT NULL,
    best_bid DECIMAL NOT NULL,
    best_ask DECIMAL NOT NULL
);

SELECT create_hypertable('liquidity_data', 'time');

-- ============================================
-- AGGREGATED METRICS TABLE
-- ============================================
CREATE TABLE aggregated_metrics (
    time TIMESTAMPTZ NOT NULL,
    token TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    tps_score DECIMAL,
    zone_score DECIMAL,
    mcdx_score DECIMAL,
    smc_score DECIMAL,
    volume_24h DECIMAL,
    volatility DECIMAL,
    sentiment DECIMAL
);

SELECT create_hypertable('aggregated_metrics', 'time');

-- ============================================
-- CONTINUOUS AGGREGATES (Real-time views)
-- ============================================
CREATE MATERIALIZED VIEW ohlcv_1h
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    token,
    FIRST(open, time) AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    LAST(close, time) AS close,
    SUM(volume) AS volume
FROM ohlcv_data
GROUP BY bucket, token;

CREATE MATERIALIZED VIEW ohlcv_4h
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('4 hours', time) AS bucket,
    token,
    FIRST(open, time) AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    LAST(close, time) AS close,
    SUM(volume) AS volume
FROM ohlcv_data
GROUP BY bucket, token;
