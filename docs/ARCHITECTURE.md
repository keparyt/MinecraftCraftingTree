# Architecture

## Goal

MinecraftCraftingTree is a deterministic compiler-like pipeline:

```text
instance files
    |
    v
source discovery
    |
    v
extractors
    |
    v
normalized facts + provenance
    |
    v
SQLite
    |
    v
production graph
    |
    +--> recursive tree
    +--> material calculation
    +--> reverse uses
    +--> path analysis
```

The key boundary is **extraction vs. analysis**. Extractors answer: "What does this source say?" The graph layer answers: "What follows from all normalized facts?"

## Why this boundary matters

Minecraft recipe JSON is data-driven, but custom recipe serializers/types exist. KubeJS can also add, remove, modify, or replace recipes during server recipe events. Therefore no single parser can safely be treated as the universal truth source. See `docs/EXTRACTION.md` for the evidence model.

## Layers

### Scanner

Read-only filesystem/JAR discovery. It detects the instance shape, mod files, possible loader/version hints, and source candidates.

### Extractors

Turn one source into normalized facts. Generic parsing handles well-understood vanilla formats. Specialized extractors are selected by installed mod ID and recipe type. Unknown data remains stored as raw data.

### Database

SQLite is the durable normalized store. It keeps relationships relational and makes incremental invalidation possible later. JSON is for export/API interchange, not for the primary store.

### Graph

The graph layer never reads JARs or parses JSON. It consumes normalized database records. This makes it testable with tiny synthetic datasets and allows future graph algorithms to evolve without rewriting source parsers.

## Runtime truth

Static scanning and loaded-game state are different evidence levels. A later runtime extractor can query the server's loaded `RecipeManager` and registries, then record those observations as `runtime` provenance. This is especially important for conditionally loaded or programmatically registered recipes.

## Design rule

Never solve incomplete data by inventing a recipe. The system should prefer:

```text
verified fact > explicit unknown > inferred fact
```

and every inference must remain distinguishable from directly extracted data.
