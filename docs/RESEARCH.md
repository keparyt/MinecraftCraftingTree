# Research Notes

This document records the external facts used to choose the foundation. It is intentionally separate from implementation notes so future changes can be checked against primary documentation.

## NeoForge 1.21.1 recipes

NeoForged documents recipe files at `data/<namespace>/recipe/<path>.json`, explains that the `type` identifies the recipe serializer, and notes that mods can define custom recipe types. The server's loaded `RecipeManager` contains the recipes actually available at runtime.

Source: https://docs.neoforged.net/docs/1.21.1/resources/server/recipes/

**Design consequence:** discover static recipe files, preserve unknown `type` values, and plan an optional runtime extractor for loaded-state validation.

## Built-in recipe types

NeoForged's 1.21.1 built-in recipe documentation describes shaped/shapeless crafting, cooking, stonecutting, and smithing serializers, including the transform serializer.

Source: https://docs.neoforged.net/docs/1.21.1/resources/server/recipes/builtin/

**Design consequence:** these are the first generic parsers, but they are not the complete universe of modded processing.

## Tags

NeoForged documents tags as lists of registered objects and places item tags under `data/<namespace>/tags/item/...`; other registries, including fluids, can also have tags. Tag composition can be additive, and tag members can be required.

Source: https://docs.neoforged.net/docs/1.21.1/resources/server/tags/

**Design consequence:** tags are first-class graph constraints; never substitute one arbitrary item for a tag.

## Resources and data packs

NeoForge treats `data` as server resources, and mods provide built-in data packs. Instance datapacks can affect recipe/tag data and resource loading.

Source: https://docs.neoforged.net/docs/1.21.1/resources/

**Design consequence:** the scanner looks beyond mod JARs and preserves source identity.

## Data load conditions

NeoForge allows `neoforge:conditions` on data files. Files can therefore exist on disk without necessarily loading into the effective server state.

Source: https://docs.neoforged.net/docs/1.21.1/resources/server/conditions/

**Design consequence:** static existence is evidence, not always runtime truth; conditions remain attached to recipes.

## Mod metadata

NeoForged documents `META-INF/neoforge.mods.toml` as the metadata file for NeoForge mod JARs, including dependencies and display information.

Source: https://docs.neoforged.net/docs/1.21.5/gettingstarted/modfiles/

**Design consequence:** metadata extraction should inspect JAR manifests before filename heuristics.

## KubeJS recipes

KubeJS documentation describes the `ServerEvents.recipes` event and supports adding, removing, modifying, and replacing recipes. The event can be reloaded and can target recipes by output/input/mod/type/ID filters.

Source: https://wiki.latvian.dev/books/kubejs/page/recipes

Current KubeJS source also contains a recipe event implementation that collects original, added, and removed recipes before applying changes.

Source: https://github.com/kube-mods/kubejs/blob/2601/src/main/java/dev/latvian/mods/kubejs/recipe/RecipesKubeEvent.java

**Design consequence:** a future KubeJS parser should model ordered mutations, rather than treating every script line as an independent static recipe.

## Conclusions

The safest architecture is therefore:

```text
STATIC SOURCES
   + JAR data
   + datapacks
   + script sources
        |
        v
NORMALIZED FACTS + PROVENANCE
        |
        +---- optional runtime validation ----+
        |                                       |
        v                                       v
              EFFECTIVE PRODUCTION GRAPH
```

Coverage should expand by extractor rather than by hardcoded item/craft definitions.
