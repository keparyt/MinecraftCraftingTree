"""Base extractor protocol shared by generic and mod-specific extractors."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from recipegraph.models import Recipe, SourceRecord

if TYPE_CHECKING:
    from recipegraph.extractors.registry import ExtractorContext


class RecipeExtractor(Protocol):
    name: str
    supported_mod_ids: frozenset[str]

    def extract(self, source: SourceRecord, context: ExtractorContext) -> Recipe:
        ...
