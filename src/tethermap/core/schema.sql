CREATE TABLE IF NOT EXISTS nodes (
  id BIGSERIAL PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('service', 'contract', 'endpoint', 'test', 'deployment')),
  name TEXT NOT NULL,
  attributes JSONB NOT NULL DEFAULT '{}',
  version INTEGER NOT NULL DEFAULT 1,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (kind, name)
);

CREATE TABLE IF NOT EXISTS node_versions (
  node_id BIGINT PRIMARY KEY,
  version INTEGER NOT NULL,
  attributes JSONB NOT NULL,
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (node_id, version)
);

CREATE TABLE IF NOT EXISTS edges (
  id BIGSERIAL PRIMARY KEY,
  source_id BIGINT NOT NULL REFERENCES nodes (id) ON DELETE CASCADE,
  target_id BIGINT NOT NULL REFERENCES nodes (id) ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK (kind IN ('provides', 'consumes', 'covers', 'deployed_as')),
  origin TEXT NOT NULL CHECK (origin IN ('confirmed', 'inferred')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (source_id, target_id, kind)
);

CREATE INDEX IF NOT EXISTS edges_target_idx ON edges (target_id);