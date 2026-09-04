"""Core data models for the normalized recipe graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ModInfo:
    mod_id: str
    name: str | None = None
    version: str | None = None
    loader: str | None = None
    minecraft_versions: list[str] = field(default_factory=list)
    authors: list[str] = field(default_factory=list)
    description: str | None = None
    file_name: str | None = None
    source_sha256: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SourceRecord:
    source_type: str
    location: str
    display_name: str | None = None
    sha256: str | None = None
    mod_id: str | None = None
    logical_path: str | None = None


@dataclass(slots=True)
class Ingredient:
    kind: str = "item"  # item, tag, fluid, alternatives, unknown
    item_id: str | None = None
    tag_id: str | None = None
    amount: float = 1.0
    probability: float = 1.0
    alternatives: list["Ingredient"] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RecipeOutput:
    kind: str = "item"
    item_id: str | None = None
    fluid_id: str | None = None
    amount: float = 1.0
    probability: float = 1.0
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Recipe:
    recipe_id: str
    recipe_type: str
    mod_id: str | None
    inputs: list[Ingredient] = field(default_factory=list)
    outputs: list[RecipeOutput] = field(default_factory=list)
    requirements: list[dict[str, Any]] = field(default_factory=list)
    catalysts: list[Ingredient] = field(default_factory=list)
    byproducts: list[RecipeOutput] = field(default_factory=list)
    source: SourceRecord | None = None
    status: str = "verified"  # verified, inferred, unsupported, invalid
    confidence: float = 1.0
    raw_data: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TagRecord:
    registry: str
    tag_id: str
    values: list[str] = field(default_factory=list)
    replace: bool = False
    source: SourceRecord | None = None


@dataclass(slots=True)
class InstanceScan:
    root: str
    minecraft_version: str | None
    loader: str | None
    loader_version: str | None
    instance_name: str
    mods: list[ModInfo] = field(default_factory=list)
    sources: list[SourceRecord] = field(default_factory=list)
    recipe_files: int = 0
    tag_files: int = 0
    script_files: int = 0
    warnings: list[str] = field(default_factory=list)
