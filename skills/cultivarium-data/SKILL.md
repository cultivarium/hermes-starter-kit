---
name: cultivarium-data
description: >
  Look up Cultivarium's public CVM strain dataset — strain inventory, genome
  assembly metadata, ORI/plasmid screen results, growth/media screen data, MIC
  antibiotic susceptibility, methylation motifs and RM gene annotations, and
  ML-predicted phenotypes (optimal temperature, pH, salinity, oxygen tolerance).
  Use whenever the user asks about a CVM strain (e.g. CVM022, CVM086) or wants
  to filter Cultivarium's strain data — which ORIs work in a strain, what
  media a strain grows in, antibiotic resistance, methylation motifs,
  predicted growth conditions, ATCC/DSM/NCBI cross-references, or genome
  download links.
---

# Cultivarium Data

Cultivarium publishes a refresh of its dataset every week as gzipped CSVs at:

```
https://dt5rr68aivik7.cloudfront.net/downloads/<file>.csv.gz
```

This skill is the entry point for querying that dataset. It documents what
each file contains and how to join across them. Files are small (a few KB
to ~3 MB), so the canonical access pattern is one `curl | gunzip` per
question — no caching layer needed.

## When to use

Trigger this skill when the user asks about:

- A specific CVM strain (e.g. "what do you know about CVM022")
- Plasmid origins of replication (ORIs) and which strains they work in
- Growth conditions, media compatibility, or doubling times for CVM strains
- Antibiotic susceptibility / MIC values for CVM strains
- Methylation motifs or restriction-modification (RM) gene annotations
- Predicted optimal temperature / pH / salinity / oxygen for a genome
- Cross-referencing a strain across ATCC, DSM, BacDive, and NCBI catalogs
- Genome assembly metadata or FASTA / annotation download URLs

Do NOT use this skill for:

- Generic NCBI genome lookups not tied to a CVM strain — use `ncbi-datasets`
- Codon optimization — use `codon-optimization`

## Datasets

| File | Contents | Reference doc |
|---|---|---|
| `cvm_strain.csv.gz` | Strain master list — CVM id, catalog number, species, source | `reference/cvm_strain.md` |
| `cvm_genome.csv.gz` | Genome assembly metadata, CheckM stats, FASTA / annotation URLs | `reference/cvm_genome.md` |
| `cvm_ori_screen.csv.gz` | Plasmid ORI screen results — fold enrichment, confidence | `reference/cvm_ori_screen.md` |
| `cvm_media_screen.csv.gz` | Growth / media screen — AUC, max OD, doubling time | `reference/cvm_media_screen.md` |
| `cvm_mic_analysis.csv.gz` | Per-antibiotic MIC90 summary | `reference/cvm_mic_analysis.md` |
| `cvm_mic90_raw_data.csv.gz` | Raw MIC concentration series (input to mic_analysis) | `reference/cvm_mic90_raw_data.md` |
| `cvm_methylation_motif.csv.gz` | Sequencing-detected methylation motifs | `reference/cvm_methylation_motif.md` |
| `cvm_methylation_gene.csv.gz` | RM gene annotations (HMM + REBASE homology) | `reference/cvm_methylation_gene.md` |
| `strain_id.csv.gz` | Strain ID cross-reference (ATCC / BacDive / DSM / NCBI / CVM) | `reference/strain_id.md` |
| `species.csv.gz` | Species taxonomy and synonyms | `reference/species.md` |
| `predicted_oxygen.csv.gz` | ML-predicted oxygen tolerance per genome | `reference/predicted_oxygen.md` |
| `predicted_ph.csv.gz` | ML-predicted optimal / min / max pH per genome | `reference/predicted_ph.md` |
| `predicted_salinity.csv.gz` | ML-predicted optimal / min / max salinity per genome | `reference/predicted_salinity.md` |
| `predicted_temperature.csv.gz` | ML-predicted optimal / min / max temperature per genome | `reference/predicted_temperature.md` |

For each question, **read the reference doc(s) for the relevant file(s)
before constructing a query** — they contain the column list, value
conventions, and join keys.

## Canonical access pattern

```bash
curl -s "https://dt5rr68aivik7.cloudfront.net/downloads/<file>.csv.gz" | gunzip
```

Pipe into standard tools — `head`, `awk`, `grep`, `cut`, `sort`, `join`,
`column -ts,`. For larger analyses see "Optional power tools" below.

### CVM id format

In every CVM-keyed file, the `cvm` column is a **bare number with leading
zeros** (`086`, `022`, `129`) — **not** the `CVM` prefix the user typically
types. Strip the prefix and zero-pad:

```bash
USER_INPUT="CVM22"
CVM_ID=$(printf '%03d' "${USER_INPUT#CVM}")   # → 022
```

When grepping, anchor on commas to avoid partial-number hits:

```bash
... | gunzip | awk -F, -v id="$CVM_ID" '$1 == id'
```

## Worked examples

### 1. Look up a strain's genome

```bash
CVM_ID=022
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_genome.csv.gz \
  | gunzip \
  | awk -F, -v id="$CVM_ID" 'NR==1 || $1==id' \
  | column -ts,
```

### 2. Which ORIs work in a strain?

```bash
CVM_ID=061
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_ori_screen.csv.gz \
  | gunzip \
  | awk -F, -v id="$CVM_ID" 'NR==1 || $1==id' \
  | column -ts,
```

Sort by fold enrichment, descending, to highlight the best-performing ORIs.
See `reference/cvm_ori_screen.md` for confidence-tier interpretation.

### 3. Cross-dataset join: strain → species name

`cvm_strain.species_id` is a numeric key into `species.id`. To list every
strain with its species name:

```bash
TMP=$(mktemp -d)
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_strain.csv.gz \
  | gunzip > "$TMP/strain.csv"
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/species.csv.gz \
  | gunzip > "$TMP/species.csv"

# join on species_id (col 3 of strain) ↔ id (col 1 of species)
awk -F, 'NR==FNR{sp[$1]=$2; next} FNR==1{print "cvm,species"; next} {print $1","sp[$3]}' \
  "$TMP/species.csv" "$TMP/strain.csv" \
  | head
```

### 4. Find every strain that grows in LB at 37 °C with high AUC

```bash
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_media_screen.csv.gz \
  | gunzip \
  | awk -F, 'NR==1 || ($2 ~ /LB/ && $3 == 37 && $7 > 0.5)' \
  | column -ts,
```

Column indices vary per file — always check `head -1` of the file before
counting columns, or read the reference doc.

## Joining the predicted_* files

The `predicted_*` files are keyed by **NCBI assembly accession** (the
numeric suffix of `GCA_<n>` / `GCF_<n>`), not by CVM id. To find
predictions for a CVM strain, go via `cvm_genome.ncbi_accession`:

```bash
CVM_ID=022
ACC=$(curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_genome.csv.gz \
  | gunzip | awk -F, -v id="$CVM_ID" '$1==id {print $8}' | head -1)
# strip GCA_/GCF_ prefix and version suffix to match the predicted_* genome column
NUM_ACC="${ACC#GC[AF]_}"
NUM_ACC="${NUM_ACC%.*}"
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/predicted_temperature.csv.gz \
  | gunzip | awk -F, -v acc="$NUM_ACC" 'NR==1 || $1==acc'
```

Many CVM strains have an empty `ncbi_accession` (genome not yet submitted
to NCBI); for those, predictions are not available in this dataset.

If the user's question is about predicted phenotypes for a non-CVM
genome — any reference assembly identified by NCBI accession or species
— use the [`genomespot-predictions`](../genomespot-predictions/) skill
instead.

## Optional power tools

For richer analyses (joins across multiple files, aggregations,
filtering by computed columns), load the CSVs into pandas or DuckDB.
Neither is bundled with the skill — install on demand:

```bash
# DuckDB can query gzipped CSVs directly over HTTPS
duckdb -c "SELECT cvm, ori_name, fold_enrichment_avg, confidence
           FROM read_csv_auto('https://dt5rr68aivik7.cloudfront.net/downloads/cvm_ori_screen.csv.gz')
           WHERE confidence = 'high'
           ORDER BY fold_enrichment_avg DESC LIMIT 20;"
```

```python
# pandas
import pandas as pd
url = "https://dt5rr68aivik7.cloudfront.net/downloads/cvm_strain.csv.gz"
df = pd.read_csv(url, compression="gzip")
```

## Refresh cadence and caveats

- A CVM id appearing in `cvm_strain` does not guarantee data in every
  per-strain file. Strains without growth data are absent from
  `cvm_media_screen`; strains without sequenced genomes are absent from
  `cvm_genome`; etc. Treat "no row" as "not measured" rather than a
  negative result.
- Join keys are the human-readable `cvm` id and species id.
