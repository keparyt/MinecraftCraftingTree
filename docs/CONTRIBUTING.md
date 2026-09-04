# Contributing

## Principles

1. **Do not invent game data.** Unsupported is better than wrong.
2. **Keep provenance.** Every normalized fact should point back to a source where possible.
3. **Keep extraction separate from graph logic.** Parsers should not recurse through production chains.
4. **Keep the scanner read-only.** Never edit user instances.
5. **Make behavior deterministic.** Sort filesystem/JAR traversal and make ranking policies explicit.
6. **Prefer primary documentation and real fixtures.** When semantics are uncertain, add a fixture and document the uncertainty.

## Adding a recipe type

Start with a synthetic JSON fixture. Implement the smallest parser that can prove the type's input/output semantics. Preserve raw fields that are not yet understood.

## Adding a mod extractor

Create a module under `recipegraph/extractors/mods/`. Register it by mod ID. Add unit tests using hand-written fixtures. Never put mod-specific branches into the core scanner or graph resolver.

## Adding graph behavior

Graph algorithms should consume normalized database records or plain model objects. They should not open ZIP files or parse JavaScript.

## Tests

Run:

```text
python -m pytest
```

No live Minecraft installation should be required for unit tests.

## Commit hygiene

Keep extraction, schema, graph, and documentation changes separable where practical. Update the research notes when a design choice depends on a version-specific external API or format.
