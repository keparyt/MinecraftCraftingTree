# MinecraftCraftingTree

Deterministic extraction and graph analysis for a complete Minecraft modpack production ecosystem.

The project intentionally contains **no AI/LLM/RAG layer**. It turns a Minecraft instance into structured, provenance-aware data that a later application or AI can query.

## Current milestone

Phase 1 + the foundation of Phase 2 are implemented:

- read-only Minecraft instance discovery
- Minecraft version / loader hints
- NeoForge/Forge/Fabric mod metadata discovery
- JAR inspection and source hashing
- discovery of recipe and tag JSON resources inside mod JARs and datapacks
- indexing of KubeJS/script sources without executing them
- normalized models for ingredients, outputs, recipes, tags, and provenance
- SQLite storage
- standard recipe parsing for shaped, shapeless, cooking, stonecutting, and smithing transforms
- preservation of unknown recipe JSON instead of silently dropping it
- scan reports and basic CLI inspection

## Commands

```text
python main.py scan D:/Minecraft/Instances/MyModpack --db ./modpack.db
python main.py mods --db ./modpack.db
python main.py report --db ./modpack.db
```

The production-tree commands (`tree`, `paths`, `materials`, `machines`, `uses`) are deliberately being added after the source/extraction foundation. This keeps graph logic independent of file-format quirks.

## Design

```text
Minecraft instance
       |
       +--> mod JARs --------+
       +--> datapacks --------+--> source discovery --> extractors
       +--> kubejs/scripts ---+
                               |
                               v
                         normalized data
                               |
                               v
                             SQLite
                               |
                               v
                         production graph
                               |
                 +-------------+-------------+
                 v             v             v
               tree          paths       materials
```

## Important correctness rule

A file existing on disk is not automatically proof that the same recipe is active at runtime. NeoForge supports conditional data loading, and datapack/resource-pack precedence can alter what is ultimately loaded. The extractor therefore keeps raw JSON, source identity, extraction status, and confidence/provenance instead of overwriting evidence with guesses.

## Documentation

- `docs/ARCHITECTURE.md` — system boundaries and data flow
- `docs/SCANNING.md` — instance/JAR/datapack discovery rules
- `docs/EXTRACTION.md` — normalized extraction contract
- `docs/DATA_MODEL.md` — entities and SQLite schema
- `docs/GRAPH.md` — planned production graph and resolver semantics
- `docs/PLUGINS.md` — extractor/plugin design
- `docs/RESEARCH.md` — external documentation verified during design
- `docs/ROADMAP.md` — phased implementation path
- `docs/CONTRIBUTING.md` — how to extend the project safely

## References

Primary references used for the foundation:

- NeoForged 1.21.1 recipes: https://docs.neoforged.net/docs/1.21.1/resources/server/recipes/
- NeoForged 1.21.1 built-in recipe types: https://docs.neoforged.net/docs/1.21.1/resources/server/recipes/builtin/
- NeoForged 1.21.1 tags: https://docs.neoforged.net/docs/1.21.1/resources/server/tags/
- NeoForged 1.21.1 resources/data packs: https://docs.neoforged.net/docs/1.21.1/resources/
- NeoForged 1.21.1 data-load conditions: https://docs.neoforged.net/docs/1.21.1/resources/server/conditions/
- KubeJS recipe event reference: https://wiki.latvian.dev/books/kubejs/page/recipes

## Status

This is an intentionally conservative foundation. Unsupported data is recorded so support can be added later without losing evidence. Coverage must grow through extractors and runtime validation, not hardcoded craft trees.
