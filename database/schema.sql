-- ============================================================================
-- Relational (SQL) Schema for Energy Demand + Weather Time-Series
-- Database: MySQL
-- Tables: locations, weather, energy_demand
-- ============================================================================

CREATE DATABASE IF NOT EXISTS energy_db;
USE energy_db;

-- 1. Locations table (where the data is collected)
CREATE TABLE IF NOT EXISTS locations (
    location_id   INT PRIMARY KEY AUTO_INCREMENT,
    city          VARCHAR(100) NOT NULL,
    country       VARCHAR(100) NOT NULL,
    region        VARCHAR(100),
    latitude      DECIMAL(9,6),
    longitude     DECIMAL(9,6),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Weather table (external variables over time)
CREATE TABLE IF NOT EXISTS weather (
    weather_id    INT PRIMARY KEY AUTO_INCREMENT,
    location_id   INT NOT NULL,
    timestamp     DATETIME NOT NULL,
    temperature_c DECIMAL(5,2),
    humidity      DECIMAL(5,2),
    wind_speed_kmh DECIMAL(5,2),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations(location_id),
    UNIQUE KEY uq_weather_location_timestamp (location_id, timestamp),
    KEY idx_weather_ts (timestamp)
);

-- 3. Energy demand table (the prediction target over time)
CREATE TABLE IF NOT EXISTS energy_demand (
    demand_id       INT PRIMARY KEY AUTO_INCREMENT,
    location_id     INT NOT NULL,
    timestamp       DATETIME NOT NULL,
    demand_mwh      DECIMAL(10,2) NOT NULL,
    is_weekend      TINYINT(1) DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations(location_id),
    UNIQUE KEY uq_demand_location_timestamp (location_id, timestamp),
    KEY idx_demand_ts (timestamp)
);

--Add the dataset location once; the API uses the same location.
INSERT INTO locations (city, country, region, latitude, longitude)
SELECT 'Valencia', 'Spain', 'Valencian Community', 39.469900, -0.376300
WHERE NOT EXISTS (
    SELECT 1 FROM locations WHERE city = 'Valencia' AND country = 'Spain'
);