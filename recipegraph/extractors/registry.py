"""Pluggable extractor registry.

Specialized extractors are selected from the installed mod IDs. The registry is deliberately
small: extraction code should not be spread through the scanner or graph layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from recipegraph.models import ModInfo, Recipe, SourceRecord
from recipegraph.extractors.generic import extract_recipe


@dataclass(frozen=True, slots=True)
class ExtractorContext:
    mods: tuple[ModInfo, ...]


Extractor = Callable[[SourceRecord, ExtractorContext], Recipe]


class ExtractorRegistry:
    def __init__(self) -> None:
        self._entries: list[tuple[str, str, Extractor]] = []
        self.register("generic", "*", lambda source, _ctx: extract_recipe(source))

    def register(self, name: str, mod_id: str, extractor: Extractor) -> None:
        self._entries.append((name, mod_id, extractor))

    def resolve(self, source: SourceRecord, mods: Iterable[ModInfo]) -> list[tuple[str, Extractor]]:
        mod_ids = {m.mod_id for m in mods}
        result: list[tuple[str, Extractor]] = []
        for name, mod_id, extractor in self._entries:
            if mod_id == "*" or source.mod_id == mod_id or mod_id in mod_ids and source.mod_id == mod_id:
                result.append((name, extractor))
        return result

    def extract(self, source: SourceRecord, context: ExtractorContext) -> tuple[str, Recipe]:
        candidates = self.resolve(source, context.mods)
        if not candidates:
            raise LookupError(f"No extractor registered for {source.location}")
        name, extractor = candidates[-1]
        return name, extractor(source, context)
