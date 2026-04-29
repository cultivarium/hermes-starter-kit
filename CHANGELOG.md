# Changelog

All notable changes to the Hermes Starter Kit are tracked here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project follows [Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-04-29

First public release.

### Skills

Six skills land in `~/.config/goose/skills/` ready for the agent to use:

- **`ncbi-datasets`** — wrap NCBI's public Datasets CLI for genome /
  sequence retrieval.
- **`codon-optimization`** — codon-optimize or harmonize a sequence
  for a target organism (self-contained Python package).
- **`protrek-search`** — search UniProt / Swiss-Prot by sequence,
  structure, or natural language via [ProTrek](https://protrek.com).
- **`pysam`** — read / write SAM / BAM / CRAM / VCF / FASTQ for NGS
  workflows. Vendored from K-Dense.
- **`gget`** — fast unified CLI / Python access to ~20 bioinformatics
  databases (gene info, BLAST, AlphaFold, enrichment). Vendored from
  K-Dense.
- **`database-lookup`** — single skill wrapping 78 public REST APIs
  (Reactome, KEGG, UniProt, STRING, PubChem, ChEMBL, Ensembl, ClinVar,
  Open Targets, etc.). Vendored from K-Dense.

### Recipes

Six recipes land in `~/.config/goose/recipes/`:

- **`onboarding`** — first-run tour. Greets the user, lists what's
  installed, points at memory and the guided setup recipes.
- **`summarize-pubmed`** — fetch and summarize recent PubMed papers on
  a topic.
- **`weekly-lit-scan`** — re-runnable literature scan that uses memory
  to track what you've already seen.
- **`create-a-skill`** — interactive walkthrough that helps you write
  a new skill from scratch.
- **`add-an-mcp-server`** — interactive walkthrough for connecting any
  MCP-speaking data source.
- **`set-up-notion`** — guided OAuth setup for the Notion remote MCP.
  Writes `notion: enabled: false` so the user toggles it on as the
  consent step in Desktop's Extensions panel.

### Installer

- macOS / Linux: `bash scripts/install.sh`.
- Windows: `irm <…>/install.ps1 | iex`.
- The installer installs skills + recipes only. It does **not** touch
  `config.yaml`, the model provider, or extension/connector setup —
  Goose's own first-run flow handles those, and our `set-up-notion`
  recipe handles per-connector wiring with explicit user consent.
- sha256-tracked idempotent updates: re-running the installer
  refreshes pristine files and leaves any user-edited skills /
  recipes alone.

### Attribution

The `pysam`, `gget`, and `database-lookup` skills are vendored from
[K-Dense AI's `claude-scientific-skills`](https://github.com/K-Dense-AI/claude-scientific-skills)
under the MIT license. Full notices and license texts are in
[`NOTICES.md`](NOTICES.md) and `vendor-licenses/k-dense/LICENSE`.

This project itself is Apache-2.0 (see [`LICENSE`](LICENSE)).
