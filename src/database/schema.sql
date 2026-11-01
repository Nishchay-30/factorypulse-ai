-- FactoryPulse AI - SQLite Schema Definition
-- Optimized for time-series industrial telemetry, WAL mode, and parameterized queries.

PRAGMA foreign_keys = ON;

-- 1. Machines Table
CREATE TABLE IF NOT EXISTS machines (
    station_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    base_rpm REAL NOT NULL,
    nominal_capacity REAL NOT NULL,
    source TEXT NOT NULL DEFAULT 'simulated',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Sensor Readings (Time-series machine telemetry with deduplication)
CREATE TABLE IF NOT EXISTS sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT UNIQUE NOT NULL,
    timestamp TEXT NOT NULL,
    station_id TEXT NOT NULL,
    source TEXT NOT NULL,
    rpm REAL NOT NULL,
    cycle_time REAL NOT NULL,
    throughput REAL NOT NULL,
    utilization REAL NOT NULL,
    queue_length INTEGER NOT NULL,
    status TEXT NOT NULL,
    vibration REAL,
    temperature REAL,
    current REAL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (station_id) REFERENCES machines(station_id)
);

CREATE INDEX IF NOT EXISTS idx_readings_time ON sensor_readings(timestamp);
CREATE INDEX IF NOT EXISTS idx_readings_station_time ON sensor_readings(station_id, timestamp);

-- 3. Production Events (Scenario changes, operator actions, overrides)
CREATE TABLE IF NOT EXISTS production_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    timestamp TEXT NOT NULL,
    station_id TEXT,
    event_type TEXT NOT NULL,
    description TEXT NOT NULL,
    details_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_time ON production_events(timestamp);

-- 4. Production Metrics (Line-level aggregated KPIs)
CREATE TABLE IF NOT EXISTS production_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT UNIQUE NOT NULL,
    timestamp TEXT NOT NULL,
    demand_rate REAL NOT NULL,
    line_throughput REAL NOT NULL,
    total_wip INTEGER NOT NULL,
    bottleneck_station TEXT,
    line_efficiency REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_metrics_time ON production_metrics(timestamp);

-- 5. AI Predictions
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id TEXT UNIQUE NOT NULL,
    timestamp TEXT NOT NULL,
    horizon_sec INTEGER NOT NULL,
    bottleneck_predicted INTEGER NOT NULL,
    predicted_station TEXT,
    risk_probability REAL NOT NULL,
    confidence REAL NOT NULL,
    model_version TEXT NOT NULL,
    features_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_predictions_time ON predictions(timestamp);

-- 6. Alerts
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id TEXT UNIQUE NOT NULL,
    timestamp TEXT NOT NULL,
    station_id TEXT NOT NULL,
    severity TEXT NOT NULL,
    alert_code TEXT NOT NULL,
    message TEXT NOT NULL,
    measured_value REAL NOT NULL,
    threshold_value REAL NOT NULL,
    acknowledged INTEGER NOT NULL DEFAULT 0,
    resolved INTEGER NOT NULL DEFAULT 0,
    acknowledged_by TEXT,
    acknowledged_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alerts_time ON alerts(timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_station_severity ON alerts(station_id, severity);

-- 7. Authenticated Users
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'operator')),
    full_name TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login TEXT
);

-- 8. Machine Learning Model Metadata
CREATE TABLE IF NOT EXISTS model_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_version TEXT UNIQUE NOT NULL,
    algorithm TEXT NOT NULL,
    trained_at TEXT NOT NULL,
    accuracy REAL NOT NULL,
    precision REAL NOT NULL,
    recall REAL NOT NULL,
    f1_score REAL NOT NULL,
    roc_auc REAL,
    parameters_json TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

