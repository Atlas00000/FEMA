-- FEMA Ops Plane Wave 1 — PostgreSQL schema
-- Applied by: python -m fema_ops db-migrate

CREATE TABLE IF NOT EXISTS certificates (
    id              TEXT PRIMARY KEY,
    version         INT NOT NULL DEFAULT 1,
    json            JSONB NOT NULL,
    active_from     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS runs (
    run_id          TEXT PRIMARY KEY,
    role            TEXT NOT NULL DEFAULT 'other',
    source          TEXT NOT NULL DEFAULT 'unknown',  -- demo | tester | auto | file
    preset          TEXT,
    symbol          TEXT,
    timeframe       TEXT,
    window_start    TEXT,
    window_end      TEXT,
    ea_build        TEXT,
    magic           TEXT,
    artifact_uri    TEXT,
    baskets_path    TEXT,
    registered_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes           TEXT,
    metrics         JSONB,
    meta            JSONB
);

CREATE INDEX IF NOT EXISTS idx_runs_source ON runs (source);
CREATE INDEX IF NOT EXISTS idx_runs_role ON runs (role);
CREATE INDEX IF NOT EXISTS idx_runs_registered ON runs (registered_at DESC);

CREATE TABLE IF NOT EXISTS baskets (
    run_id          TEXT NOT NULL REFERENCES runs (run_id) ON DELETE CASCADE,
    basket_id       TEXT NOT NULL,
    open_time       TEXT,
    close_time      TEXT,
    symbol          TEXT,
    direction       TEXT,
    open_level      INT,
    max_depth       INT,
    profit          DOUBLE PRECISION,
    exit_reason     TEXT,
    hit_tp          INT,
    hit_bsl         INT,
    mae             DOUBLE PRECISION,
    mfe             DOUBLE PRECISION,
    bars_alive      INT,
    spread_points   INT,
    payload         JSONB,
    schema_version  TEXT DEFAULT 'fema_baskets_v2',
    PRIMARY KEY (run_id, basket_id)
);

CREATE INDEX IF NOT EXISTS idx_baskets_close ON baskets (run_id, close_time);

CREATE TABLE IF NOT EXISTS events (
    id              BIGSERIAL PRIMARY KEY,
    run_id          TEXT NOT NULL REFERENCES runs (run_id) ON DELETE CASCADE,
    ts              TEXT,
    event_type      TEXT,
    payload         JSONB
);

CREATE INDEX IF NOT EXISTS idx_events_run ON events (run_id);

CREATE TABLE IF NOT EXISTS health_snapshots (
    id              BIGSERIAL PRIMARY KEY,
    ts              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    run_id          TEXT,
    source          TEXT,
    score           DOUBLE PRECISION,
    ladder          TEXT,
    would_pause_new BOOLEAN,
    components      JSONB,
    cert_version    TEXT,
    raw             JSONB
);

CREATE INDEX IF NOT EXISTS idx_health_ts ON health_snapshots (ts DESC);

CREATE TABLE IF NOT EXISTS sync_heartbeats (
    id              BIGSERIAL PRIMARY KEY,
    ts              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source          TEXT NOT NULL,
    last_mtime      TEXT,
    bytes           BIGINT,
    rows            INT,
    ok              BOOLEAN NOT NULL DEFAULT TRUE,
    detail          JSONB
);

CREATE INDEX IF NOT EXISTS idx_sync_ts ON sync_heartbeats (ts DESC);
