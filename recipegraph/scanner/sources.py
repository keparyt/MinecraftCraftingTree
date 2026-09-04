"""Read-only discovery of recipe/tag/script source files."""

from __future__ import annotations

import hashlib
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from recipegraph.models import ModInfo, SourceRecord


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iter_zip_data(path: Path, mod_id: str | None) -> list[SourceRecord]:
    records: list[SourceRecord] = []
    try:
        with ZipFile(path) as archive:
            for name in sorted(archive.namelist()):
                normalized = name.replace("\\", "/")
                lower = normalized.lower()
                if not lower.endswith((".json", ".js", ".zs", ".kts")):
                    continue
                is_recipe = "/recipe/" in f"/{lower}" or "/recipes/" in f"/{lower}"
                is_tag = "/tags/" in f"/{lower}"
                if not (is_recipe or is_tag):
                    continue
                records.append(
                    SourceRecord(
                        source_type="mod_jar",
                        location=f"{path}!/{normalized}",
                        display_name=path.name,
                        sha256=_sha256_bytes(archive.read(name)),
                        mod_id=mod_id,
                        logical_path=normalized,
                    )
                )
    except (BadZipFile, OSError):
        return records
    return records


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def discover_sources(root: Path, mods: list[ModInfo]) -> list[SourceRecord]:
    sources: list[SourceRecord] = []
    mod_by_name = {m.file_name: m for m in mods if m.file_name}

    mods_dir = root / "mods"
    if mods_dir.is_dir():
        for jar in sorted(mods_dir.glob("*.jar")):
            mod = mod_by_name.get(jar.name)
            sources.extend(_iter_zip_data(jar, mod.mod_id if mod else None))

    # External datapacks/resources are discovered without changing the instance.
    for base_name in ("datapacks", "resourcepacks"):
        base = root / base_name
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".json", ".mcmeta", ".js", ".zs"}:
                continue
            logical = path.relative_to(base).as_posix()
            lower = logical.lower()
            if "/recipe/" not in f"/{lower}" and "/recipes/" not in f"/{lower}" and "/tags/" not in f"/{lower}":
                continue
            sources.append(
                SourceRecord(
                    source_type="datapack" if base_name == "datapacks" else "resourcepack",
                    location=str(path),
                    display_name=base_name,
                    sha256=_sha256_file(path),
                    logical_path=logical,
                )
            )

    for script_root in (root / "kubejs", root / "scripts"):
        if not script_root.is_dir():
            continue
        source_type = "kubejs" if script_root.name.lower() == "kubejs" else "script"
        for path in sorted(script_root.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".js", ".mjs", ".zs", ".kts"}:
                sources.append(
                    SourceRecord(
                        source_type=source_type,
                        location=str(path),
                        display_name=script_root.name,
                        sha256=_sha256_file(path),
                        logical_path=path.relative_to(root).as_posix(),
                    )
                )

    return sources
