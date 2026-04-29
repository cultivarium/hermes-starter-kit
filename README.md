# Hermes Starter Kit

A pre-configured starter kit for [Goose](https://goose-docs.ai/), the
open-source AI agent — aimed at research teams who want a working "AI
scientist" on their machine without a week of setup.

The kit installs on top of a vanilla Goose install. It does not fork
Goose, replace its UI, or run any server of its own. It only adds:

- a small bundle of [skills](skills/) for biology research workflows
- a set of [recipes](recipes/) — short tours, literature-scan
  workflows, and guided setup helpers (e.g. wiring up Notion as a
  data source)

The kit deliberately **does not** modify Goose's `config.yaml`, choose
your model provider, or wire up extensions for you. Goose's own
first-run flow handles provider/API-key entry, and the kit's
`set-up-notion` recipe walks you through adding a connector when you
want one.

Everything lives under `~/.config/goose/` (macOS / Linux) or
`%APPDATA%\Block\goose\config\` (Windows). The kit never writes
secrets to disk — anything sensitive goes in the OS keyring via
Goose itself.

## 60-second install

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/cultivarium/hermes-starter-kit/stable/scripts/install.sh | bash
```

**Windows (PowerShell):**

```powershell
irm https://raw.githubusercontent.com/cultivarium/hermes-starter-kit/stable/scripts/install.ps1 | iex
```

If Goose isn't installed yet, the script offers to run the official AAIF
installer first.

## What you get

| Skill | What it does |
|---|---|
| [`ncbi-datasets`](skills/ncbi-datasets/) | Wrap NCBI's public Datasets CLI for genome/sequence retrieval. |
| [`codon-optimization`](skills/codon-optimization/) | Codon-optimize or harmonize a sequence for a target organism. |
| [`protrek-search`](skills/protrek-search/) | Search UniProt / Swiss-Prot by sequence, structure, or natural language via [ProTrek](https://protrek.com). |
| [`pysam`](skills/pysam/) | Read/write SAM/BAM/CRAM/VCF/FASTQ for NGS workflows. Needs `samtools`/`bcftools` on the host. |
| [`gget`](skills/gget/) | Fast unified CLI/Python access to ~20 bioinformatics databases (gene info, BLAST, AlphaFold). |
| [`database-lookup`](skills/database-lookup/) | Single skill wrapping 78 public REST APIs (Reactome, KEGG, UniProt, STRING, PubChem, ChEMBL, Ensembl, ClinVar, …). |

The `pysam`, `gget`, and `database-lookup` skills are vendored from
[K-Dense's `claude-scientific-skills`](https://github.com/K-Dense-AI/claude-scientific-skills)
under the MIT license. Full attribution and license texts are in
[NOTICES.md](NOTICES.md).

| Recipe | What it does |
|---|---|
| [`onboarding`](recipes/onboarding.yaml) | First-run tour. Confirms what's installed and saves a setup note to memory. |
| [`summarize-pubmed`](recipes/summarize-pubmed.yaml) | Fetch and summarize recent PubMed papers on a topic. |
| [`weekly-lit-scan`](recipes/weekly-lit-scan.yaml) | Re-runnable literature scan that uses memory to track what you've already seen. |
| [`create-a-skill`](recipes/create-a-skill.yaml) | Interactive walkthrough that helps you write a new skill from scratch. |
| [`add-an-mcp-server`](recipes/add-an-mcp-server.yaml) | Interactive walkthrough for connecting any MCP-speaking data source. |
| [`set-up-notion`](recipes/set-up-notion.yaml) | Guided setup for the kit's Notion connector — writes the right config block and walks you through Goose Desktop's Extensions UI. |
| [`update-kit`](recipes/update-kit.yaml) | Pulls the latest skills and recipes from the public starter kit repo. Files you've edited locally are preserved. |

## First run

1. Open Goose (Desktop or CLI). On first run it will prompt you for a
   model provider — Anthropic, OpenAI, or Ollama. Pick whichever you
   have a key for; Goose stores the key in your OS keyring.

2. Try the onboarding recipe:

   ```
   goose recipe run onboarding
   ```

   It tours what's installed and confirms memory is persisting across
   runs.

3. Want Goose to talk to your Notion workspace? Run the guided setup:

   ```
   goose recipe run set-up-notion
   ```

## Updating

Two ways:

- **From inside Goose** (easiest): run the `update-kit` recipe from
  the Recipes panel. It runs the kit's update script, summarizes
  what changed, and prompts you to restart Goose Desktop.
- **From a terminal**: re-run the installer.

  ```bash
  bash ~/.config/goose/.starter-kit/scripts/install.sh
  ```

Either path is idempotent: pristine files are refreshed, files
you've edited locally are left alone.

## Customising

The kit is meant to be a starting point, not a finished product. Once
installed, files under `~/.config/goose/skills/` and
`~/.config/goose/recipes/` are yours — edit them, add more, copy them
into another agent. The next install run will detect your edits via
sha256 fingerprint and won't clobber them.

## Docs

- [Provider setup](docs/PROVIDERS.md) — Anthropic, OpenAI, Ollama
- [Connector setup](docs/CONNECTORS.md) — Notion (today), gdrive (next)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## License

Apache-2.0. See [LICENSE](LICENSE).
