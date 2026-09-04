"""Command-line interface for the extractor foundation."""

from __future__ import annotations

import argparse
import json
import sqlite3
import time
from pathlib import Path

from recipegraph.database.repository import set_scan_metadata, upsert_mods, upsert_recipe, upsert_sources, upsert_tag
from recipegraph.database.schema import connect
from recipegraph.extractors.generic import extract_recipe, extract_tag
from recipegraph.models import InstanceScan
from recipegraph.scanner.instance import InstanceScanner


def _add_db_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--db", default="recipegraph.db", help="SQLite database path (outside the instance by default)")


def scan_command(args: argparse.Namespace) -> int:
    started = time.perf_counter()
    scanner = InstanceScanner(args.instance)
    result = scanner.scan()
    connection = connect(args.db)
    try:
        upsert_mods(connection, result.mods)
        upsert_sources(connection, result.sources)
        recipes = 0
        tags = 0
        errors = list(result.warnings)
        for source in result.sources:
            if not source.logical_path:
                continue
            logical = "/" + source.logical_path.replace("\\", "/") + "/"
            try:
                if "/recipe/" in logical or "/recipes/" in logical:
                    recipe = extract_recipe(source)
                    upsert_recipe(connection, recipe)
                    recipes += 1
                    errors.extend(f"{recipe.recipe_id}: {w}" for w in recipe.warnings)
                elif "/tags/" in logical:
                    upsert_tag(connection, extract_tag(source))
                    tags += 1
            except Exception as exc:
                errors.append(f"{source.location}: {type(exc).__name__}: {exc}")
        duration = time.perf_counter() - started
        set_scan_metadata(connection, {
            "instance": result.root,
            "instance_name": result.instance_name,
            "minecraft_version": result.minecraft_version,
            "loader": result.loader,
            "loader_version": result.loader_version,
            "mods": len(result.mods),
            "source_files": len(result.sources),
            "recipes": recipes,
            "tags": tags,
            "scripts": result.script_files,
            "errors": errors,
            "duration_seconds": round(duration, 4),
        })
        connection.commit()
    finally:
        connection.close()

    print(f"Scanned: {result.root}")
    print(f"Minecraft: {result.minecraft_version or 'unknown'}")
    print(f"Loader: {result.loader or 'unknown'} {result.loader_version or ''}".rstrip())
    print(f"Mods: {len(result.mods)}")
    print(f"Recipes indexed: {recipes}")
    print(f"Tags indexed: {tags}")
    print(f"Scripts indexed: {result.script_files}")
    if errors:
        print(f"Warnings/errors: {len(errors)} (see scan_metadata.errors)")
    return 0


def mods_command(args: argparse.Namespace) -> int:
    connection = connect(args.db)
    rows = connection.execute("SELECT mod_id, name, version, loader, file_name FROM mods ORDER BY mod_id").fetchall()
    try:
        for row in rows:
            name = row[1] or row[0]
            version = row[2] or "?"
            loader = row[3] or "?"
            file_name = row[4] or "?"
            print(f"{row[0]:30} {version:16} {loader:10} {name} [{file_name}]")
    finally:
        connection.close()
    return 0


def report_command(args: argparse.Namespace) -> int:
    connection = connect(args.db)
    rows = connection.execute("SELECT key, value FROM scan_metadata ORDER BY key").fetchall()
    data = {row[0]: json.loads(row[1]) for row in rows}
    connection.close()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        for key, value in data.items():
            print(f"{key}: {value}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="recipegraph", description="MinecraftCraftingTree deterministic extractor")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="scan a Minecraft instance")
    scan.add_argument("instance", type=Path)
    _add_db_argument(scan)
    scan.set_defaults(func=scan_command)

    mods = subparsers.add_parser("mods", help="list mods from a scanned database")
    _add_db_argument(mods)
    mods.set_defaults(func=mods_command)

    report = subparsers.add_parser("report", help="show the latest scan metadata")
    _add_db_argument(report)
    report.add_argument("--json", action="store_true")
    report.set_defaults(func=report_command)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
