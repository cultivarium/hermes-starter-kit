---
name: genomespot-predictions
description: >
  Look up GenomeSPOT-predicted growth conditions — optimal / minimum / maximum
  temperature, pH, salinity, and oxygen tolerance — for a sequenced genome by
  its NCBI assembly accession (`GCA_*` / `GCF_*`). Covers tens of thousands of
  bacterial and archaeal genomes. Use whenever the user asks about predicted
  growth optima for an organism by NCBI accession or species, wants to identify
  thermophiles / psychrophiles / halophiles / alkaliphiles / anaerobes by
  prediction, or needs growth-condition predictions for a genome that is not a
  CVM strain.
---

# GenomeSPOT Predictions

[GenomeSPOT](https://github.com/cultivarium/GenomeSPOT) is a machine-learning
model that predicts the growth conditions an organism prefers from its
genome sequence alone. Cultivarium publishes the predictions for a broad
corpus of bacterial and archaeal genomes — keyed by NCBI assembly accession
— as gzipped CSVs at:

```
https://dt5rr68aivik7.cloudfront.net/downloads/<file>.csv.gz
```

Files are small (a few hundred KB each) so the canonical access pattern
is one `curl | gunzip` per question.

## When to use

Trigger this skill when the user asks about:

- Predicted optimal / minimum / maximum growth temperature, pH, or salinity
  for a genome
- Predicted oxygen tolerance (aerobic vs. anaerobic) from genome sequence
- Filtering many genomes for thermophiles, psychrophiles, halophiles,
  alkaliphiles, acidophiles, or anaerobes
- Predicted growth conditions for a genome identified by NCBI assembly
  accession (`GCA_*` / `GCF_*`) or by species
- Predicted growth conditions for a CVM strain (resolve the strain to
  its NCBI accession first — see "Cross-reference with a CVM strain"
  below)

Do NOT use this skill for:

- Measured (rather than predicted) growth conditions — use
  `cultivarium-data` for CVM strain growth screens, or consult an
  experimental dataset.
- NCBI genome metadata or downloads — use `ncbi-datasets`.

## Datasets

| File | Contents | Reference doc |
|---|---|---|
| `predicted_temperature.csv.gz` | Predicted optimal / min / max growth temperature (°C) | `reference/predicted_temperature.md` |
| `predicted_ph.csv.gz` | Predicted optimal / min / max pH | `reference/predicted_ph.md` |
| `predicted_salinity.csv.gz` | Predicted optimal / min / max NaCl (%) | `reference/predicted_salinity.md` |
| `predicted_oxygen.csv.gz` | Predicted oxygen tolerance class | `reference/predicted_oxygen.md` |

Each file covers tens of thousands of genomes (`predicted_temperature`
alone has ~16k rows). For each question, **read the reference doc(s) for
the relevant file(s) before constructing a query** — they document column
semantics, value vocabularies, and confidence-tier interpretation.

## Canonical access pattern

```bash
curl -s "https://dt5rr68aivik7.cloudfront.net/downloads/<file>.csv.gz" | gunzip
```

## Genome accession format

The `genome` column in every predicted_* file is the **numeric suffix** of
the NCBI assembly accession — no `GCA_` / `GCF_` prefix. The
`genome_version` column carries the full accession. To look up a
prediction from a user-supplied `GCA_003675855.1`, strip both the prefix
and the version suffix:

```bash
INPUT="GCA_003675855.1"
ACC="${INPUT#GC[AF]_}"   # → 003675855.1
ACC="${ACC%.*}"          # → 003675855
```

## Worked examples

### 1. Predicted optimal temperature for a single genome

```bash
ACC=003675855
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/predicted_temperature.csv.gz \
  | gunzip \
  | awk -F, -v acc="$ACC" 'NR==1 || $1==acc' \
  | column -ts,
```

### 2. Find every confidently-thermophilic genome (optimum ≥ 50 °C)

```bash
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/predicted_temperature.csv.gz \
  | gunzip \
  | awk -F, 'NR==1 || ($3 >= 50 && $10 == "high")' \
  | column -ts,
```

### 3. Find genomes predicted to be both halophilic and alkaliphilic

```bash
TMP=$(mktemp -d)
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/predicted_salinity.csv.gz \
  | gunzip > "$TMP/sal.csv"
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/predicted_ph.csv.gz \
  | gunzip > "$TMP/ph.csv"

# join on genome (col 1); keep rows where salinity optimum > 5 % AND pH optimum > 9
awk -F, 'NR==FNR && FNR>1 && $3>5 && $10=="high" {sal[$1]=1; next}
         FNR==1 {print "genome,ph_opt,sal_opt"; next}
         ($1 in sal) && $3>9 && $10=="high" {print $1","$3",present"}' \
  "$TMP/sal.csv" "$TMP/ph.csv"
```

### 4. Cross-reference with a CVM strain

If the user gives a CVM id and wants the prediction, use the join via
`cvm_genome.ncbi_accession` documented in the
[`cultivarium-data`](../cultivarium-data/) skill, then look up the
resulting accession here.

## Optional power tools

For larger analyses (joining all four files, aggregating, filtering by
computed columns), load the CSVs into pandas or DuckDB. Neither is
bundled — install on demand:

```bash
duckdb -c "SELECT genome, optimum, confidence
           FROM read_csv_auto('https://dt5rr68aivik7.cloudfront.net/downloads/predicted_temperature.csv.gz')
           WHERE optimum >= 50 AND confidence = 'high'
           ORDER BY optimum DESC LIMIT 50;"
```

```python
import pandas as pd
url = "https://dt5rr68aivik7.cloudfront.net/downloads/predicted_temperature.csv.gz"
df = pd.read_csv(url, compression="gzip")
```

## Refresh cadence and caveats

- Predictions are computed from genome content — they are not
  experimental measurements. Treat them as priors, not ground truth.
- The `is_novel = t` flag marks genomes outside the model's training
  distribution; treat those predictions with extra caution regardless of
  the `confidence` tier.
- Coverage is by NCBI assembly accession. A genome that has not been
  submitted to NCBI is not in the dataset.
