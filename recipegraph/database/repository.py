"""Persistence layer for normalized scan data."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict

from recipegraph.models import Ingredient, Recipe, SourceRecord, TagRecord


def _source_id(connection: sqlite3.Connection, source: SourceRecord | None) -> int | None:
    if source is None:
        return None
    row = connection.execute("SELECT id FROM sources WHERE location = ?", (source.location,)).fetchone()
    return int(row[0]) if row else None


def upsert_mods(connection: sqlite3.Connection, mods) -> None:
    for mod in mods:
        connection.execute(
            """INSERT INTO mods VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(mod_id) DO UPDATE SET
              name=excluded.name, version=excluded.version, loader=excluded.loader,
              minecraft_versions_json=excluded.minecraft_versions_json,
              authors_json=excluded.authors_json, description=excluded.description,
              file_name=excluded.file_name, source_sha256=excluded.source_sha256,
              metadata_json=excluded.metadata_json""",
            (
                mod.mod_id,
                mod.name,
                mod.version,
                mod.loader,
                json.dumps(mod.minecraft_versions),
                json.dumps(mod.authors),
                mod.description,
                mod.file_name,
                mod.source_sha256,
                json.dumps(mod.metadata, sort_keys=True),
            ),
        )


def upsert_sources(connection: sqlite3.Connection, sources) -> None:
    for source in sources:
        connection.execute(
            """INSERT INTO sources(source_type, location, display_name, sha256, mod_id, logical_path)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(location) DO UPDATE SET
              source_type=excluded.source_type, display_name=excluded.display_name,
              sha256=excluded.sha256, mod_id=excluded.mod_id, logical_path=excluded.logical_path""",
            (
                source.source_type,
                source.location,
                source.display_name,
                source.sha256,
                source.mod_id,
                source.logical_path,
            ),
        )


def _insert_item(connection: sqlite3.Connection, item_id: str | None, source: str) -> None:
    if not item_id or ":" not in item_id or item_id.startswith("#"):
        return
    namespace, item_path = item_id.split(":", 1)
    connection.execute(
        "INSERT OR IGNORE INTO items(item_id, namespace, item_path, source) VALUES (?, ?, ?, ?)",
        (item_id, namespace, item_path, source),
    )


def _insert_ingredient(connection: sqlite3.Connection, recipe_id: str, position: int, value: Ingredient) -> None:
    connection.execute(
        """INSERT INTO recipe_inputs
        (recipe_id, position, kind, item_id, tag_id, amount, probability, alternatives_json, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            recipe_id,
            position,
            value.kind,
            value.item_id,
            value.tag_id,
            value.amount,
            value.probability,
            json.dumps([asdict(v) for v in value.alternatives], sort_keys=True),
            json.dumps(value.data, sort_keys=True),
        ),
    )
    _insert_item(connection, value.item_id, "recipe_input")


def upsert_recipe(connection: sqlite3.Connection, recipe: Recipe) -> None:
    source_id = _source_id(connection, recipe.source)
    connection.execute(
        """INSERT INTO recipes(recipe_id, recipe_type, mod_id, status, confidence, source_id, raw_json, warnings_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(recipe_id) DO UPDATE SET
          recipe_type=excluded.recipe_type, mod_id=excluded.mod_id, status=excluded.status,
          confidence=excluded.confidence, source_id=excluded.source_id,
          raw_json=excluded.raw_json, warnings_json=excluded.warnings_json""",
        (
            recipe.recipe_id,
            recipe.recipe_type,
            recipe.mod_id,
            recipe.status,
            recipe.confidence,
            source_id,
            json.dumps(recipe.raw_data, sort_keys=True),
            json.dumps(recipe.warnings),
        ),
    )
    connection.execute("DELETE FROM recipe_inputs WHERE recipe_id = ?", (recipe.recipe_id,))
    connection.execute("DELETE FROM recipe_outputs WHERE recipe_id = ?", (recipe.recipe_id,))
    connection.execute("DELETE FROM recipe_requirements WHERE recipe_id = ?", (recipe.recipe_id,))
    connection.execute("DELETE FROM recipe_catalysts WHERE recipe_id = ?", (recipe.recipe_id,))

    for index, ingredient in enumerate(recipe.inputs):
        _insert_ingredient(connection, recipe.recipe_id, index, ingredient)
    for index, output in enumerate(recipe.outputs):
        connection.execute(
            """INSERT INTO recipe_outputs
            (recipe_id, position, kind, item_id, fluid_id, amount, probability, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                recipe.recipe_id, index, output.kind, output.item_id, output.fluid_id,
                output.amount, output.probability, json.dumps(output.data, sort_keys=True),
            ),
        )
        _insert_item(connection, output.item_id, "recipe_output")
    for index, requirement in enumerate(recipe.requirements):
        connection.execute(
            "INSERT INTO recipe_requirements(recipe_id, position, kind, value_json) VALUES (?, ?, ?, ?)",
            (recipe.recipe_id, index, str(requirement.get("kind", "unknown")), json.dumps(requirement, sort_keys=True)),
        )


def upsert_tag(connection: sqlite3.Connection, tag: TagRecord) -> None:
    source_id = _source_id(connection, tag.source)
    connection.execute(
        """INSERT OR REPLACE INTO tags(tag_id, registry, replace_flag, source_id)
        VALUES (?, ?, ?, ?)""",
        (tag.tag_id, tag.registry, int(tag.replace), source_id),
    )
    connection.execute(
        "DELETE FROM tag_members WHERE registry = ? AND tag_id = ? AND source_id IS ?",
        (tag.registry, tag.tag_id, source_id),
    )
    for member in tag.values:
        is_tag = int(member.startswith("#"))
        member_id = member[1:] if is_tag else member
        connection.execute(
            """INSERT INTO tag_members(registry, tag_id, member_id, is_tag, required, source_id)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (tag.registry, tag.tag_id, member_id, is_tag, 1, source_id),
        )


def set_scan_metadata(connection: sqlite3.Connection, values: dict[str, object]) -> None:
    for key, value in values.items():
        connection.execute(
            "INSERT INTO scan_metadata(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, json.dumps(value, sort_keys=True)),
        )
