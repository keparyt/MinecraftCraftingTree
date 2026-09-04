# Extraction

## Evidence model

Every normalized recipe carries:

- `source`: where the information came from
- `status`: `verified`, `inferred`, `unsupported`, or `invalid`
- `confidence`: numeric quality score
- `raw_data`: original JSON when available
- `warnings`: parser problems or unsupported semantics

This prevents a parser from silently turning an unknown format into a false recipe.

## Generic recipe handling

The first parser recognizes common vanilla serializers:

```text
minecraft:crafting_shaped
minecraft:crafting_shapeless
minecraft:smelting
minecraft:blasting
minecraft:smoking
minecraft:campfire_cooking
minecraft:stonecutting
minecraft:smithing_transform
minecraft:smithing_trim
minecraft:smithing
```

NeoForge's 1.21.1 documentation confirms that the recipe `type` selects a serializer, and that mods may define custom recipe types. This is why the extractor stores unsupported types instead of dropping them.

## Ingredient model

An ingredient may be:

```text
EXACT ITEM
TAG
FLUID
ALTERNATIVES
UNKNOWN
```

A tag must never be replaced with one arbitrary item. The graph resolver will later resolve tag membership as an OR-set while preserving the original tag identity.

## Outputs

Outputs carry amount and a probability value. The initial generic layer records probabilities when fields such as `chance` or `probability` are directly present; it does not infer distributions that are not encoded by the source.

## Conditions

NeoForge can attach `neoforge:conditions` to data. A static parser can record these conditions, but it cannot always prove that they evaluate true for the exact running instance/world. Therefore condition evaluation is a future environment-aware stage, not a reason to silently delete the source.

## KubeJS

KubeJS recipe events can add, remove, modify, and replace recipes. A script-level parser therefore needs to model both **additive definitions** and **mutations of existing recipes**. It must preserve operation order and identify targets by recipe ID/output/input/mod/type when those filters are used.

The correct long-term design is:

```text
static JSON
   |
KubeJS script operations
   |
runtime-loaded recipes (optional validation)
   v
effective recipe set
```

## Specialized extractors

A specialized extractor should only parse semantics it can prove. For example, a Create extractor can map mechanical pressing or mixing into machine/processing requirements, but it should not invent a machine requirement when the source data does not establish one.
