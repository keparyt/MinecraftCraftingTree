"""Generic extraction of standard JSON recipes and tags.

This module intentionally does not guess semantics for unknown recipe types. It stores
those recipes as unsupported raw data so a dedicated extractor can handle them later.
"""

from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

from recipegraph.models import Ingredient, Recipe, RecipeOutput, SourceRecord, TagRecord

STANDARD_TYPES = {
    "minecraft:crafting_shaped",
    "minecraft:crafting_shapeless",
    "minecraft:smelting",
    "minecraft:blasting",
    "minecraft:smoking",
    "minecraft:campfire_cooking",
    "minecraft:stonecutting",
    "minecraft:smithing_transform",
    "minecraft:smithing_trim",
    "minecraft:smithing",
}


def _load_json(source: SourceRecord) -> dict:
    if "!/" in source.location:
        archive_name, member = source.location.split("!/", 1)
        with ZipFile(archive_name) as archive:
            return json.loads(archive.read(member))
    return json.loads(Path(source.location).read_text(encoding="utf-8"))


def _ingredient(value: object, amount: float = 1.0) -> Ingredient:
    if isinstance(value, str):
        if value.startswith("#"):
            return Ingredient(kind="tag", tag_id=value[1:], amount=amount)
        return Ingredient(kind="item", item_id=value, amount=amount)
    if isinstance(value, list):
        return Ingredient(kind="alternatives", amount=amount, alternatives=[_ingredient(v) for v in value])
    if isinstance(value, dict):
        count = float(value.get("count", value.get("amount", amount)))
        if "tag" in value:
            return Ingredient(kind="tag", tag_id=str(value["tag"]), amount=count, data=value)
        if "item" in value:
            return Ingredient(kind="item", item_id=str(value["item"]), amount=count, data=value)
        if "fluid" in value:
            return Ingredient(kind="fluid", item_id=str(value["fluid"]), amount=count, data=value)
        if "items" in value and isinstance(value["items"], list):
            return Ingredient(
                kind="alternatives",
                amount=count,
                alternatives=[_ingredient(v) for v in value["items"]],
                data=value,
            )
    return Ingredient(kind="unknown", amount=amount, data={"raw": value})


def _output(value: object, default_amount: float = 1.0) -> RecipeOutput:
    if isinstance(value, str):
        return RecipeOutput(item_id=value, amount=default_amount)
    if isinstance(value, dict):
        item_id = value.get("id", value.get("item"))
        if item_id is not None:
            return RecipeOutput(
                kind="item",
                item_id=str(item_id),
                amount=float(value.get("count", default_amount)),
                probability=float(value.get("chance", value.get("probability", 1.0))),
                data=value,
            )
        if "fluid" in value:
            return RecipeOutput(
                kind="fluid",
                fluid_id=str(value["fluid"]),
                amount=float(value.get("amount", default_amount)),
                probability=float(value.get("chance", value.get("probability", 1.0))),
                data=value,
            )
    return RecipeOutput(kind="unknown", amount=default_amount, data={"raw": value})


def recipe_id_from_source(source: SourceRecord) -> str:
    logical = source.logical_path or source.location
    normalized = logical.replace("\\", "/")
    if normalized.startswith("data/"):
        normalized = normalized[5:]
    for marker in ("/recipe/", "/recipes/"):
        if marker in normalized:
            namespace, rest = normalized.split(marker, 1)
            if rest.endswith(".json"):
                rest = rest[:-5]
            return f"{namespace}:{rest}"
    return normalized


def extract_recipe(source: SourceRecord) -> Recipe:
    raw = _load_json(source)
    recipe_id = recipe_id_from_source(source)
    recipe_type = str(raw.get("type", "unknown"))
    recipe = Recipe(
        recipe_id=recipe_id,
        recipe_type=recipe_type,
        mod_id=source.mod_id or recipe_id.split(":", 1)[0],
        source=source,
        raw_data=raw,
    )

    if recipe_type not in STANDARD_TYPES:
        recipe.status = "unsupported"
        recipe.confidence = 0.0
        recipe.warnings.append(f"Unsupported recipe type: {recipe_type}")
        return recipe

    if recipe_type == "minecraft:crafting_shaped":
        pattern = raw.get("pattern", [])
        key = raw.get("key", {})
        for row in pattern:
            for symbol in row:
                if symbol.strip():
                    recipe.inputs.append(_ingredient(key.get(symbol)))
        result = raw.get("result")
        if result is not None:
            recipe.outputs.append(_output(result))

    elif recipe_type == "minecraft:crafting_shapeless":
        recipe.inputs.extend(_ingredient(v) for v in raw.get("ingredients", []))
        result = raw.get("result")
        if result is not None:
            recipe.outputs.append(_output(result))

    elif recipe_type in {
        "minecraft:smelting",
        "minecraft:blasting",
        "minecraft:smoking",
        "minecraft:campfire_cooking",
        "minecraft:stonecutting",
    }:
        value = raw.get("ingredient")
        if value is None:
            value = raw.get("input")
        if value is not None:
            recipe.inputs.append(_ingredient(value))
        result = raw.get("result", raw.get("output"))
        if result is not None:
            recipe.outputs.append(_output(result))
        if "cookingtime" in raw:
            recipe.requirements.append({"kind": "processing_time", "ticks": raw["cookingtime"]})
        recipe.requirements.extend(
            {"kind": key, "value": raw[key]}
            for key in ("experience", "category")
            if key in raw
        )

    elif recipe_type in {"minecraft:smithing_transform", "minecraft:smithing", "minecraft:smithing_trim"}:
        for field in ("base", "template", "addition"):
            if field in raw:
                recipe.inputs.append(_ingredient(raw[field]))
        if "result" in raw:
            recipe.outputs.append(_output(raw["result"]))
        elif recipe_type == "minecraft:smithing_trim":
            # The resulting item is derived from the base plus the trim template;
            # the JSON does not identify one fixed output registry ID.
            recipe.outputs.append(RecipeOutput(kind="unknown", data={"dynamic_output": "smithing_trim"}))
            recipe.warnings.append("Smithing trim has a dynamic output; no fixed item ID was fabricated")
            recipe.confidence = 0.8
        recipe.requirements.append({"kind": "smithing_slot_order", "fields": ["base", "template", "addition"]})

    if not recipe.outputs:
        recipe.status = "invalid"
        recipe.confidence = 0.0
        recipe.warnings.append("No output could be extracted")
    return recipe


def extract_tag(source: SourceRecord) -> TagRecord:
    raw = _load_json(source)
    logical = (source.logical_path or "").replace("\\", "/")
    parts = logical.split("/")
    try:
        tags_index = parts.index("tags")
        registry = "/".join(parts[tags_index + 1 : tags_index + 2])
        tag_path = "/".join(parts[tags_index + 2 :])
    except ValueError:
        registry = "unknown"
        tag_path = logical
    if tag_path.endswith(".json"):
        tag_path = tag_path[:-5]
    namespace = parts[1] if len(parts) > 1 and parts[0] == "data" else "unknown"
    tag_id = f"{namespace}:{tag_path}"
    values = []
    for value in raw.get("values", []):
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, dict) and "id" in value:
            values.append(str(value["id"]))
    return TagRecord(registry=registry, tag_id=tag_id, values=values, replace=bool(raw.get("replace", False)), source=source)
