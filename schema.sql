-- schema.sql

-- Store AI role outputs (coach, gm, scout, defense, council)
CREATE TABLE IF NOT EXISTS runs (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMPTZ DEFAULT NOW(),
    kind TEXT NOT NULL,
    week INT,
    json JSONB
);

-- Store snapshots of raw API pulls
CREATE TABLE IF NOT EXISTS snapshots (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMPTZ DEFAULT NOW(),
    source TEXT NOT NULL,
    data JSONB
);

-- Opponent surveillance
CREATE TABLE IF NOT EXISTS opponents (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMPTZ DEFAULT NOW(),
    manager TEXT,
    roster JSONB,
    moves JSONB,
    tendencies JSONB
);
