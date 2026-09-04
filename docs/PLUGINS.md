# Extractor Plugins

## Goal

Adding a new mod must not require editing the scanner, database core, or graph resolver.

The intended extension point is an extractor registered for one or more mod IDs and/or recipe types.

```text
ExtractorRegistry
      |
      +-- generic vanilla extractor
      +-- kubejs extractor
      +-- create extractor
      +-- mekanism extractor
      +-- ...
```

## Activation

Specialized extractors should activate only when their target mod is present. This prevents assumptions about mods that are not installed.

## Contract

An extractor receives a source plus context and returns normalized `Recipe`, `TagRecord`, machine/process records, or explicit unsupported results. It may inspect raw JSON but must not mutate the source.

## Priority

A practical order is:

1. exact runtime data, when available
2. exact mod-provided structured data
3. generic serializer parsing
4. script/source parsing
5. clearly labeled inference

When two extractors describe the same recipe, provenance must make the conflict visible. Do not silently pick whichever parser ran last.

## Create

Create needs a dedicated extractor because its production ecosystem includes processes such as pressing, crushing, milling, mixing, cutting, deploying, haunting, washing, bulk processing, spout filling, sequenced assembly, and mechanical crafting. The extractor should map those semantics to machine/process requirements rather than flattening them into ordinary crafting ingredients.

Create support belongs here, not scattered across graph code.

## KubeJS

KubeJS is source-oriented: recipe definitions can be created or mutated during the server recipe event. The parser should eventually build an ordered operation model so additions/removals/replacements can be replayed deterministically.

## Testing an extractor

Every specialized extractor should include synthetic fixtures covering:

- normal recipe
- multiple outputs
- tags and alternatives
- catalysts
- conditions
- malformed input
- unknown fields
- duplicate/conflicting sources

No test should require a live Minecraft installation unless it is explicitly marked as an integration test.
