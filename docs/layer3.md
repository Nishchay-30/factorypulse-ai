# Layer 3 — Synthetic Data → MQTT → HiveMQ → SQLite → Dashboard
## Schema Design, WAL Mode, Deduplication & Historical Analytics

### 1. Objective
Store all validated machine telemetry, line metrics, alerts, predictions, users, and model metadata in an indexed SQLite database configured in WAL mode.

### 2. Implemented Components
- **Schema Definition:** `src/database/schema.sql`
  - 8 relational tables: `machines`, `sensor_readings`, `production_events`, `production_metrics`, `predictions`, `alerts`, `users`, `model_metadata`.
  - Indexes on timestamp and station_id for fast analytics.
- **Data Access Layer (DAL):** `src/database/db.py`
  - Single-writer thread synchronization preventing SQLite lock collisions.
  - Parameterized queries eliminating SQL injection.
  - Deduplication on `message_id` via `ON CONFLICT(message_id) DO NOTHING`.
- **Database Ingestion Service:** `src/ingestion/db_ingestor.py`
- **Historical Analytics View:** `dashboard/app.py` (Historical Analytics page with one-click CSV export).

### 3. How to Run & Verify
```bash
# Execute Layer 3 acceptance test
bash scripts/run_layer3.sh
```

### 4. Acceptance Criteria Checklist
- [x] Schema initialized with all 8 tables and indexes.
- [x] WAL journal mode configured for high concurrency.
- [x] Deduplication protects against duplicate network messages.
- [x] Historical data persists across application restarts.
- [x] CSV export of telemetry and production metrics operational.

