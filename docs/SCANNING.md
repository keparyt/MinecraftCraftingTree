# Scanning

## Input contract

Input is a Minecraft instance directory. The scanner never writes into it. Output databases/reports are separate paths supplied to the CLI.

Expected locations are discovered opportunistically:

```text
mods/
config/
defaultconfigs/
kubejs/
scripts/
datapacks/
resourcepacks/
saves/
versions/
```

Missing directories are warnings, not fatal errors.

## Mod discovery

Every `mods/*.jar` is inspected as a ZIP archive. Metadata priority is:

1. `META-INF/neoforge.mods.toml`
2. `META-INF/mods.toml`
3. `fabric.mod.json`
4. filename fallback

For each JAR we record a SHA-256 hash. The hash is the foundation for future incremental scanning.

NeoForge documents `neoforge.mods.toml` as the mod metadata file and uses dependency sections in the same format. See the research notes for the version-specific references.

## Resource discovery

A JAR can contain server data exposed through its `data/` namespace tree. Recipe resources normally live under:

```text
data/<namespace>/recipe/<path>.json
```

Tag files are under the corresponding `tags/<registry>/...` path. The scanner also checks instance datapacks for these resources.

## KubeJS

`kubejs/` and `scripts/` are indexed, but scripts are **not executed** by this Python scanner. Script execution would be unsafe and would make results non-deterministic. Parsing of supported KubeJS recipe APIs belongs in a dedicated source parser; runtime execution belongs to a separate optional runtime extractor.

## Version detection

Version detection uses instance `versions/<version>/<version>.json` entries when available and prefers plain semantic Minecraft version directory names. It is only a hint at this stage: a future environment resolver should also inspect launcher/profile metadata and loader installation files.

## Read-only invariant

No extractor may:

- rewrite a JAR
- create files inside the instance
- modify configs
- launch scripts by default
- mutate a Minecraft world

If a future runtime mode launches Minecraft, it must live behind an explicit separate command and process boundary.
