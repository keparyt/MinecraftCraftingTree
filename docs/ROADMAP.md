# Roadmap

## Phase 1 — Scanner ✅ foundation

- instance validation
- Minecraft version hints
- mod JAR discovery
- NeoForge/Forge/Fabric metadata discovery
- JAR hashing
- recipe/tag source discovery
- KubeJS/script indexing
- read-only invariant

## Phase 2 — Generic data ✅ foundation

- normalized models
- SQLite schema
- standard recipe parsing
- tag parsing
- unknown recipe preservation
- provenance/status/confidence

## Phase 3 — Complete graph

- load normalized facts into an in-memory graph
- producer/consumer indexes
- recursive tree resolver
- cycle detection
- full alternative-path retention
- tag expansion with logical OR semantics

## Phase 4 — Quantities and resource accounting

- requested amount propagation
- recipe execution rounding
- guaranteed vs expected resources
- catalysts and container returns
- byproducts

## Phase 5 — Processes

- fluid inputs/outputs
- machine requirements
- heat/speed/pressure/stress
- energy systems without unsafe cross-system conversions
- complex multi-step processes

## Phase 6 — Mod extractors

Prioritize mods actually present in the scanned pack. Create is a high priority, followed by other major recipe/process systems found in the instance.

## Phase 7 — Effective recipe set

- KubeJS operation replay
- datapack precedence
- NeoForge condition evaluation where enough environment data exists
- conflict diagnostics
- runtime `RecipeManager` extraction as an optional separate backend

## Phase 8 — Export/API

- stable JSON schema
- Mermaid
- DOT
- GraphML
- Python API
- machine-readable scan reports

## Phase 9 — Incremental scanning

- source hash cache
- extractor/version fingerprints
- selective invalidation
- unchanged-source reuse

## Phase 10 — Verification

Compare generated results against a live 1.21.1 NeoForge instance and recipe viewer where appropriate. Differences become fixtures or extractor issues; they are not silently patched with guesses.
