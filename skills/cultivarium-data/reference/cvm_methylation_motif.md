# cvm_methylation_motif.csv.gz

URL: `https://dt5rr68aivik7.cloudfront.net/downloads/cvm_methylation_motif.csv.gz`

Sequencing-detected DNA methylation motifs per CVM strain. Motifs are
called from long-read (Nanopore / PacBio) basecalling. Each row is one
(strain × motif) combination.

## Columns

| Column | Description |
|---|---|
| `cvm` | Strain id. |
| `motif` | Canonical motif string with methylated position(s) annotated (e.g. `GATC`, `CCWGG`). |
| `motif_raw` | The motif as originally emitted by the caller, before canonicalization. |
| `methylation_type` | `4mC` (4-methylcytosine), `5mC` (5-methylcytosine), or `6mA` (N6-methyladenine). |
| `genome_site` | Total number of occurrences of the motif in the genome. |
| `methylated_site` | Number of those occurrences detected as methylated. |
| `methylation_coverage` | `methylated_site / genome_site` — fraction of motif occurrences that are methylated. |
| `average_percent_methylation_per_site` | Mean fraction of reads supporting methylation at each methylated site. |
| `methylated_position_1` | Position within the motif of the first methylated base (0-indexed). |
| `methylated_position_1_percent` | Fraction of methylation calls falling at position 1. |
| `methylated_position_2` | Position of the second methylated base, when present. |
| `methylated_position_2_percent` | Fraction of methylation calls at position 2. |

## Cross-reference

- `cvm_methylation_gene.csv.gz` lists the RM (restriction-modification)
  genes annotated in the genome that may produce these motifs. Joining
  motif → producing methyltransferase requires checking the
  `homolog_motif` column in the gene file.

## Examples

```bash
# all motifs detected for a strain
CVM_ID=022
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_methylation_motif.csv.gz \
  | gunzip | awk -F, -v id="$CVM_ID" 'NR==1 || $1==id' | column -ts,
```

```bash
# every strain with a 6mA GATC methylation
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_methylation_motif.csv.gz \
  | gunzip | awk -F, 'NR==1 || ($2=="GATC" && $4=="6mA")' | column -ts,
```
