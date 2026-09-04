"""SQLite schema and initialization."""

from __future__ import annotations

import sqlite3

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS scan_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mods (
    mod_id TEXT PRIMARY KEY,
    name TEXT,
    version TEXT,
    loader TEXT,
    minecraft_versions_json TEXT NOT NULL,
    authors_json TEXT NOT NULL,
    description TEXT,
    file_name TEXT,
    source_sha256 TEXT,
    metadata_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY,
    source_type TEXT NOT NULL,
    location TEXT NOT NULL UNIQUE,
    display_name TEXT,
    sha256 TEXT,
    mod_id TEXT REFERENCES mods(mod_id),
    logical_path TEXT
);

CREATE TABLE IF NOT EXISTS recipes (
    recipe_id TEXT PRIMARY KEY,
    recipe_type TEXT NOT NULL,
    mod_id TEXT REFERENCES mods(mod_id),
    status TEXT NOT NULL,
    confidence REAL NOT NULL,
    source_id INTEGER REFERENCES sources(id),
    raw_json TEXT NOT NULL,
    warnings_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS items (
    item_id TEXT PRIMARY KEY,
    namespace TEXT NOT NULL,
    item_path TEXT NOT NULL,
    source TEXT
);

CREATE TABLE IF NOT EXISTS fluids (
    fluid_id TEXT PRIMARY KEY,
    namespace TEXT NOT NULL,
    fluid_path TEXT NOT NULL,
    source TEXT
);

CREATE TABLE IF NOT EXISTS machines (
    machine_id TEXT PRIMARY KEY,
    name TEXT,
    mod_id TEXT REFERENCES mods(mod_id),
    machine_type TEXT,
    source TEXT,
    raw_json TEXT
);

CREATE TABLE IF NOT EXISTS tags (
    tag_id TEXT NOT NULL,
    registry TEXT NOT NULL,
    replace_flag INTEGER NOT NULL DEFAULT 0,
    source_id INTEGER REFERENCES sources(id),
    PRIMARY KEY (registry, tag_id, source_id)
);

CREATE TABLE IF NOT EXISTS tag_members (
    registry TEXT NOT NULL,
    tag_id TEXT NOT NULL,
    member_id TEXT NOT NULL,
    is_tag INTEGER NOT NULL DEFAULT 0,
    required INTEGER NOT NULL DEFAULT 1,
    source_id INTEGER REFERENCES sources(id)
);

CREATE TABLE IF NOT EXISTS recipe_inputs (
    id INTEGER PRIMARY KEY,
    recipe_id TEXT NOT NULL REFERENCES recipes(recipe_id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    kind TEXT NOT NULL,
    item_id TEXT,
    tag_id TEXT,
    amount REAL NOT NULL,
    probability REAL NOT NULL,
    alternatives_json TEXT NOT NULL,
    raw_json TEXT
);

CREATE TABLE IF NOT EXISTS recipe_outputs (
    id INTEGER PRIMARY KEY,
    recipe_id TEXT NOT NULL REFERENCES recipes(recipe_id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    kind TEXT NOT NULL,
    item_id TEXT,
    fluid_id TEXT,
    amount REAL NOT NULL,
    probability REAL NOT NULL,
    raw_json TEXT
);

CREATE TABLE IF NOT EXISTS recipe_requirements (
    id INTEGER PRIMARY KEY,
    recipe_id TEXT NOT NULL REFERENCES recipes(recipe_id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    kind TEXT NOT NULL,
    value_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS recipe_catalysts (
    id INTEGER PRIMARY KEY,
    recipe_id TEXT NOT NULL REFERENCES recipes(recipe_id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    kind TEXT NOT NULL,
    item_id TEXT,
    tag_id TEXT,
    amount REAL NOT NULL,
    raw_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_recipe_outputs_item ON recipe_outputs(item_id);
CREATE INDEX IF NOT EXISTS idx_recipe_inputs_item ON recipe_inputs(item_id);
CREATE INDEX IF NOT EXISTS idx_recipe_inputs_tag ON recipe_inputs(tag_id);
CREATE INDEX IF NOT EXISTS idx_recipe_type ON recipes(recipe_type);
CREATE INDEX IF NOT EXISTS idx_sources_mod ON sources(mod_id);
"""


def connect(path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    return connection
