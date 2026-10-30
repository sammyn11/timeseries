-- ============================================================================
-- Relational (SQL) Schema for Energy Demand + Weather Time-Series
-- Database: MySQL (tested with SQLite for portability)
-- Tables: locations, weather, energy_demand  (minimum 3 tables required)
-- ============================================================================

DROP TABLE IF EXISTS energy_demand;
DROP TABLE IF EXISTS weather;
DROP TABLE IF EXISTS locations;

-- 1. Locations table (where the data is collected)
CREATE TABLE locations (
    location_id   INT PRIMARY KEY AUTO_INCREMENT,
    city          VARCHAR(100) NOT NULL,
    country       VARCHAR(100) NOT NULL,
    region        VARCHAR(100),
    latitude      DECIMAL(9,6),
    longitude     DECIMAL(9,6),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Weather table (external variables over time)
CREATE TABLE weather (
    weather_id    INT PRIMARY KEY AUTO_INCREMENT,
    location_id   INT NOT NULL,
    timestamp     DATETIME NOT NULL,
    temperature_c DECIMAL(5,2),
    humidity      DECIMAL(5,2),
    wind_speed_kmh DECIMAL(5,2),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations(location_id),
    UNIQUE (location_id, timestamp)
);

-- 3. Energy demand table (the prediction target over time)
CREATE TABLE energy_demand (
    demand_id       INT PRIMARY KEY AUTO_INCREMENT,
    location_id     INT NOT NULL,
    timestamp       DATETIME NOT NULL,
    demand_mwh      DECIMAL(10,2) NOT NULL,
    is_weekend      TINYINT(1) DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations(location_id),
    UNIQUE (location_id, timestamp)
);

-- Indexes for fast time-series range queries
CREATE INDEX idx_weather_ts   ON weather(timestamp);
CREATE INDEX idx_demand_ts    ON energy_demand(timestamp);

-- Sample insert (one location)
INSERT INTO locations (city, country, region, latitude, longitude)
VALUES ('Sample City', 'Sample Country', 'Central', 40.7128, -74.0060);