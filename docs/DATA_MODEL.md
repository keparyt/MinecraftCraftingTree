# Data Model

## Core entities

### Mod

Identifies a discovered mod JAR and stores metadata plus source hash.

### Source

A provenance record for a source file/resource. Important fields are source type, physical location, logical data path, mod ID, and SHA-256.

### Item / Fluid / Machine

Registry objects are first-class entities. The current schema has item/fluid/machine tables even before all extractors populate them, so graph requirements do not need a schema rewrite later.

### Recipe

A recipe is a transformation record:

```text
id
 type
 mod
 inputs[]
 outputs[]
 requirements[]
 catalysts[]
 byproducts[]
 source
 status
 confidence
 raw_data
```

### Tag

Tags are keyed by both registry and tag ID. Members can point to exact registry objects or another tag.

## Database relationships

```text
MOD ──< SOURCE ──< RECIPE
                  │
                  ├──< INPUT ──> ITEM/TAG/FLUID
                  ├──< OUTPUT ─> ITEM/FLUID
                  ├──< REQUIREMENT
                  └──< CATALYST

TAG ──< TAG_MEMBER ──> ITEM or TAG
```

## Why raw JSON is kept

Normalized fields are for deterministic graph queries. Raw JSON is the evidence trail used to add support later, diagnose parser bugs, and compare extraction versions.

## Quantity semantics

Quantities should remain numeric and unrounded until a calculation stage explicitly requests execution counts. The future resolver will use ceiling division for recipes that output discrete item counts, while probability/expected-value calculations remain separate from guaranteed resource requirements.

## Identity

Registry IDs are the primary identity for items/fluids. Display names are metadata only and must never be used as graph keys.
