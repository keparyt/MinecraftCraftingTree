"""Minecraft instance discovery. Read-only by design."""

from __future__ import annotations

from pathlib import Path

from recipegraph.models import InstanceScan, ModInfo, SourceRecord
from recipegraph.scanner.mods import inspect_mod_jar
from recipegraph.scanner.sources import discover_sources


KNOWN_SOURCE_DIRS = (
    "mods",
    "config",
    "defaultconfigs",
    "kubejs",
    "scripts",
    "datapacks",
    "resourcepacks",
    "saves",
    "versions",
)


class InstanceScanner:
    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()

    def validate(self) -> None:
        if not self.root.exists():
            raise FileNotFoundError(f"Minecraft instance does not exist: {self.root}")
        if not self.root.is_dir():
            raise NotADirectoryError(f"Minecraft instance is not a directory: {self.root}")

    def _detect_version(self) -> str | None:
        versions_dir = self.root / "versions"
        candidates: list[str] = []
        if versions_dir.is_dir():
            for directory in sorted(p for p in versions_dir.iterdir() if p.is_dir()):
                version_json = directory / f"{directory.name}.json"
                if version_json.is_file():
                    candidates.append(directory.name)
        for candidate in candidates:
            if candidate.count(".") >= 1 and candidate[0].isdigit():
                # Prefer plain Minecraft semantic versions over loader folder names.
                parts = candidate.split(".")
                if all(part.isdigit() for part in parts):
                    return candidate
        return candidates[0] if candidates else None

    @staticmethod
    def _detect_loader(mods: list[ModInfo]) -> tuple[str | None, str | None]:
        counts: dict[str, int] = {}
        versions: dict[str, set[str]] = {}
        for mod in mods:
            if not mod.loader:
                continue
            counts[mod.loader] = counts.get(mod.loader, 0) + 1
            if mod.version:
                versions.setdefault(mod.loader, set()).add(mod.version)
        if not counts:
            return None, None
        loader = max(counts, key=counts.get)
        loader_version = ", ".join(sorted(versions.get(loader, set()))) or None
        return loader, loader_version

    def scan(self) -> InstanceScan:
        self.validate()
        mods_dir = self.root / "mods"
        mods: list[ModInfo] = []
        warnings: list[str] = []

        if mods_dir.is_dir():
            for jar in sorted(mods_dir.glob("*.jar")):
                try:
                    mods.append(inspect_mod_jar(jar))
                except Exception as exc:  # one bad JAR must not stop a whole scan
                    warnings.append(f"Failed to inspect {jar.name}: {type(exc).__name__}: {exc}")
        else:
            warnings.append("mods/ directory was not found")

        sources = discover_sources(self.root, mods)
        loader, loader_version = self._detect_loader(mods)
        scan = InstanceScan(
            root=str(self.root),
            minecraft_version=self._detect_version(),
            loader=loader,
            loader_version=loader_version,
            instance_name=self.root.name,
            mods=mods,
            sources=sources,
            warnings=warnings,
        )
        scan.recipe_files = sum(1 for s in sources if s.logical_path and "/recipe/" in f"/{s.logical_path}")
        scan.tag_files = sum(1 for s in sources if s.logical_path and "/tags/" in f"/{s.logical_path}")
        scan.script_files = sum(1 for s in sources if s.source_type in {"kubejs", "script"})
        return scan
