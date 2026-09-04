"""Mod JAR metadata inspection."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
from zipfile import ZipFile

from recipegraph.models import ModInfo
from recipegraph.scanner.sources import _sha256_file


_MC_VERSION_RE = re.compile(r"\b1\.\d+(?:\.\d+)?\b")


def _first_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _parse_toml(raw: bytes, jar_name: str, digest: str, loader: str, metadata_format: str) -> ModInfo | None:
    data = tomllib.loads(raw.decode("utf-8"))
    mods = data.get("mods") or []
    if not mods or not isinstance(mods, list) or not isinstance(mods[0], dict):
        return None
    mod = mods[0]
    mod_id = _first_string(mod.get("modId"))
    if not mod_id:
        return None
    dependencies: list[dict[str, object]] = []
    value = data.get("dependencies", {})
    if isinstance(value, dict):
        dep_value = value.get(mod_id, [])
        if isinstance(dep_value, list):
            dependencies = [d for d in dep_value if isinstance(d, dict)]
    versions = sorted(set(_MC_VERSION_RE.findall(str(mod.get("loaderVersion", "")))))
    authors_value = mod.get("authors")
    authors = [authors_value] if isinstance(authors_value, str) else [str(v) for v in authors_value] if isinstance(authors_value, list) else []
    return ModInfo(
        mod_id=mod_id,
        name=_first_string(mod.get("displayName")),
        version=_first_string(mod.get("version")),
        loader=loader,
        minecraft_versions=versions,
        authors=authors,
        description=_first_string(mod.get("description")),
        file_name=jar_name,
        source_sha256=digest,
        metadata={"dependencies": dependencies, "metadata_format": metadata_format, "loader_version_constraint": mod.get("loaderVersion")},
    )


def _parse_fabric_json(raw: bytes, jar_name: str, digest: str) -> ModInfo | None:
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        return None
    mod_id = _first_string(data.get("id"))
    if not mod_id:
        return None
    authors_value = data.get("authors", [])
    authors = [a.get("name", str(a)) if isinstance(a, dict) else str(a) for a in authors_value] if isinstance(authors_value, list) else []
    return ModInfo(
        mod_id=mod_id,
        name=_first_string(data.get("name")),
        version=_first_string(data.get("version")),
        loader="fabric",
        minecraft_versions=[],
        authors=authors,
        description=_first_string(data.get("description")),
        file_name=jar_name,
        source_sha256=digest,
        metadata={"dependencies": data.get("depends", {}), "environment": data.get("environment"), "metadata_format": "json"},
    )


def inspect_mod_jar(path: str | Path) -> ModInfo:
    path = Path(path)
    digest = _sha256_file(path)
    with ZipFile(path) as archive:
        names = set(archive.namelist())
        if "META-INF/neoforge.mods.toml" in names:
            result = _parse_toml(archive.read("META-INF/neoforge.mods.toml"), path.name, digest, "neoforge", "neoforge_toml")
            if result:
                return result
        if "META-INF/mods.toml" in names:
            result = _parse_toml(archive.read("META-INF/mods.toml"), path.name, digest, "forge", "forge_toml")
            if result:
                return result
        if "fabric.mod.json" in names:
            result = _parse_fabric_json(archive.read("fabric.mod.json"), path.name, digest)
            if result:
                return result

    return ModInfo(
        mod_id=path.stem,
        file_name=path.name,
        source_sha256=digest,
        metadata={"metadata_format": "unknown"},
    )
