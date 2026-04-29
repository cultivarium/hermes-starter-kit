---
name: codon-optimization
description: Use when the user needs to codon-optimize, harmonize, or reverse-translate a DNA or protein sequence for expression in a target organism.
---

# Codon Optimization

Perform codon optimization, codon harmonization, and reverse translation of DNA/protein sequences using the bundled `codonopt` CLI.

## Setup

The `codonopt` package is bundled in this skill's directory. Determine the skill directory path from where this SKILL.md is located, then run all commands with:

```bash
uv run --directory <path/to/codon-optimization/> codonopt <subcommand> [options]
```

## Important: Sequence Input Best Practices

**Avoid passing sequences through conversation context.** Long sequences are at risk of truncation and transcription errors when copy-pasted into the chat.

- **If the user pastes a raw sequence into the chat**, warn them that this is risky for long sequences, and ask them to upload the sequence as a FASTA file instead. Ask the user to attach the FASTA file or paste a path to a local file. When the user attaches a file, the agent's harness will expose it at an absolute path; use that path directly.
- **When you have sequence files on disk** (e.g., downloaded via ncbi-datasets or another tool), pass the file path directly or read the file. Do not copy the full sequence into your context.
- **Prefer writing output to files** with `-o output.fasta` rather than printing full sequences in your response, especially for sequences >500 bp.

```bash
# Read a coding sequence from an uploaded FASTA file (extract sequence without header lines)
SEQ=$(grep -v '>' <path-to-attached-file>/mysequence.fasta | tr -d '\n')
uv run --directory <skill_dir> codonopt optimize "$SEQ" --target 316407 -o optimized.fasta
```

## Step 1: Identify the Task

Parse the user's request:

- **Optimize**: Has a DNA or protein sequence, wants it optimized for a target organism (maximize expression)
- **Harmonize**: Wants to re-encode a sequence while preserving translational pausing patterns from the native host
- **Reverse-translate**: Has a protein sequence, wants an optimized DNA sequence

## Step 2: Obtain a Codon Usage Table

There are exactly three ways to obtain a codon usage table for the target (or source) organism:

1. **From a FASTA genome file** — Prodigal gene prediction identifies CDS regions, then codons are counted. Best approach for your genomes or user uploaded genomes.
2. **From a GenBank genome file** — Annotated CDS features are extracted directly. Best for assemblies retrieved from NCBI.
3. **From the Kazusa database via NCBI TaxID** — Pass a numeric TaxID (e.g. `316407` for *E. coli*) to `--target` or `--source` and the codon table is fetched live from the Kazusa codon usage database. Use this for animals and plants or organisms with very, very large genomes (>500 Mbp).

### Obtaining genome files

Use the **`ncbi-datasets` skill** to download annotated genomes for any organism with an NCBI assembly. The key files are:
- **GenBank (`.gbff`)** — annotated genome with CDS features
- **FASTA (`.fna`)** — raw nucleotide sequence (genes will be predicted with Prodigal)

Example using ncbi-datasets:
```bash
# Download the RefSeq genome for Akkermansia muciniphila (taxid 239935)
datasets download genome taxon 239935 --reference-only --include gbff --filename akkermansia.zip
unzip akkermansia.zip
# GenBank file at: ncbi_dataset/data/<accession>/<accession>_genomic.gbff
```

Fetch the genome FASTA from NCBI (the ncbi-datasets skill is one option) or from the user's local filesystem.

### Compute the codon usage table

```bash
# Compute codon usage table from a GenBank file (uses annotated CDS features)
uv run --directory <skill_dir> codonopt compute-table ncbi_dataset/data/GCF_000436395.1/GCF_000436395.1_genomic.gbff \
  --output akkermansia_codon_table.json

# Compute codon usage table from a FASTA file (uses Prodigal gene prediction)
uv run --directory <skill_dir> codonopt compute-table genome.fasta --output codon_table.json

# Force a format when the extension is non-standard
uv run --directory <skill_dir> codonopt compute-table genome.dat --format fasta --output codon_table.json
```

The `compute-table` command auto-detects format by extension (`.gb`/`.gbk`/`.gbff` for GenBank; `.fa`/`.fasta`/`.fna` for FASTA). For FASTA files, it runs Prodigal gene prediction to identify coding sequences before counting codons.

### Use genome files directly (skip compute-table)

Instead of a two-step workflow, you can pass genome files directly to `optimize` and `harmonize`:

```bash
# Optimize using a FASTA genome as the target codon source
uv run --directory <skill_dir> codonopt optimize ATGAAA... --target-fasta genome.fasta -o optimized.fasta

# Optimize using a GenBank genome as the target codon source
uv run --directory <skill_dir> codonopt optimize ATGAAA... --target-genbank genome.gbff -o optimized.fasta

# Harmonize with genome files for both source and target
uv run --directory <skill_dir> codonopt harmonize ATGAAA... \
  --source-fasta native_genome.fasta \
  --target-genbank expression_host.gbff

# Mix and match: Kazusa TaxID for source, FASTA genome for target
uv run --directory <skill_dir> codonopt harmonize ATGAAA... \
  --source 316407 \
  --target-fasta novel_host.fasta
```

For each command, only one target source and one source source is allowed (e.g., you cannot combine `--target` with `--target-fasta`).

### Pre-computed tables still work

```bash
# Use a pre-computed JSON table
uv run --directory <skill_dir> codonopt optimize ATGAAA... \
  --codon-table akkermansia_codon_table.json -o optimized.fasta

# Harmonization with pre-computed tables
uv run --directory <skill_dir> codonopt harmonize ATGAAA... \
  --source-codon-table native_org_table.json \
  --codon-table akkermansia_codon_table.json
```

## Step 3: Run the Command

### Codon Optimization

Replaces each codon with a synonym that maximizes expression in the target organism.

```bash
# DNA input with Kazusa TaxID
uv run --directory <skill_dir> codonopt optimize <SEQUENCE> --target <taxid>

# Protein input (reverse-translates then optimizes)
uv run --directory <skill_dir> codonopt optimize <SEQUENCE> --target <taxid> --input-type protein

# Frequency-matching mode (less aggressive; preserves codon diversity)
uv run --directory <skill_dir> codonopt optimize <SEQUENCE> --target <taxid> --method match_usage

# Save optimized sequence to a FASTA file
uv run --directory <skill_dir> codonopt optimize <SEQUENCE> --target <taxid> -o output.fasta

# Use a genome file directly as the codon source
uv run --directory <skill_dir> codonopt optimize <SEQUENCE> --target-fasta genome.fasta
uv run --directory <skill_dir> codonopt optimize <SEQUENCE> --target-genbank genome.gbff

# Pre-computed codon usage table (JSON or CSV)
uv run --directory <skill_dir> codonopt optimize <SEQUENCE> --codon-table path/to/table.json
```

### Codon Harmonization

Preserves the relative codon usage pattern of the source organism when re-encoding for a target host. Use this when native-like translational pausing (and thus protein folding) matters more than maximizing CAI.

```bash
# DNA input with Kazusa TaxIDs
uv run --directory <skill_dir> codonopt harmonize <SEQUENCE> --source <source_taxid> --target <target_taxid>

# Protein input
uv run --directory <skill_dir> codonopt harmonize <SEQUENCE> --source <source_taxid> --target <target_taxid> --input-type protein

# Custom codon tables
uv run --directory <skill_dir> codonopt harmonize <SEQUENCE> \
  --source-codon-table source_table.json \
  --codon-table target_table.json

# Genome files as source and/or target
uv run --directory <skill_dir> codonopt harmonize <SEQUENCE> \
  --source-fasta native_genome.fasta \
  --target-genbank expression_host.gbff
```

## Step 4: Report Results

Present the key metrics and the output sequence to the user.

**For optimization:**
- Target organism and method used
- CAI before → after (Codon Adaptation Index; 1.0 = all optimal codons)
- GC content of the optimized sequence
- Number of codons changed out of total
- The full optimized DNA sequence

**For harmonization:**
- Source and target organisms
- CAI of original and harmonized sequence (in the target organism's context)
- Number of codons changed
- The full harmonized DNA sequence

Always give the output sequence directly so the user can copy it.

## Key Concepts

- **CAI (Codon Adaptation Index)**: 0–1 score; 1.0 means every codon is the highest-frequency synonym for that amino acid in the target organism. Higher = better adapted for expression.
- **best_codon** (default): Replaces every codon with the most frequent synonym. Maximizes CAI. Best for maximizing protein yield.
- **match_usage**: Adjusts codon frequencies to match the target organism's overall profile without forcing all-best codons. Less aggressive; useful when you want diversity without sacrificing too much expression.
- **harmonize**: Maps Relative Codon Adaptiveness (RCA) values from the source organism to the target. Preserves the translational "pausing" pattern of the original gene, which can help complex proteins fold correctly.
- **Codon tables**: Can be obtained three ways: (a) from a FASTA genome via Prodigal gene prediction (`--target-fasta`/`--source-fasta`), (b) from a GenBank genome via CDS annotations (`--target-genbank`/`--source-genbank`), or (c) from the Kazusa database via NCBI TaxID (`--target`/`--source`). Kazusa tables are genome-wide and differ from expression-weighted tables used by commercial tools (GenScript, IDT).

## Example Commands

```bash
# Optimize GFP (DNA) for E. coli (TaxID 316407)
uv run --directory <skill_dir> codonopt optimize ATGAGTAAAGGAGAAGAACTTTTCACTGG --target 316407

# Reverse-translate human insulin and optimize for E. coli
uv run --directory <skill_dir> codonopt optimize MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKT \
  --target 316407 --input-type protein

# Harmonize MSP1-42 from P. falciparum (TaxID 36329) to E. coli
uv run --directory <skill_dir> codonopt harmonize ATGAAA... \
  --source 36329 --target 316407

# Optimize for a non-model organism using its genome FASTA
uv run --directory <skill_dir> codonopt optimize ATGAAA... --target-fasta novel_host.fasta -o optimized.fasta
```

## Notes

- DNA sequences must start with `ATG` and have length divisible by 3
- Protein sequences must start with `M` (methionine)
- Sequences can be piped via stdin: `echo "ATGAAA..." | uv run --directory <skill_dir> codonopt optimize --target 316407`
- The `-o output.fasta` flag writes a FASTA file (useful for longer sequences)
