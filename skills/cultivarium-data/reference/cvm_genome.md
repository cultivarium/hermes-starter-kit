# cvm_genome.csv.gz

URL: `https://dt5rr68aivik7.cloudfront.net/downloads/cvm_genome.csv.gz`

Genome assembly metadata for sequenced CVM strains. One row per
genome (a strain may have multiple sequenced genomes if re-sequenced).
Includes CheckM quality stats and download URLs for the FASTA and
Bakta annotation bundle.

## Columns

| Column | Description |
|---|---|
| `cvm` | Strain id. Joins to `cvm_strain.cvm`. |
| `genome_size` | Total assembly length in base pairs. |
| `contig_number` | Number of contigs in the assembly. Lower is better; `1` indicates a closed genome. |
| `checkm_completeness` | CheckM-estimated genome completeness (%). ≥95 is high quality, <90 is incomplete. |
| `sequencing_technology` | Platform — `Illumina`, `Nanopore`, `PacBio`, or hybrid combinations. |
| `fasta_url` | HTTPS link to the assembled FASTA (public S3 — no auth needed). |
| `annotation_url` | HTTPS link to a Bakta annotation zip. |
| `ncbi_accession` | NCBI assembly accession (`GCA_*` / `GCF_*`) when the genome has been submitted; empty otherwise. |

CheckM contamination is not present in this dataset — only the
completeness percentage is included.

## Joins

- `cvm` → `cvm_strain.cvm` for species and source repository.
- `ncbi_accession` (with the `GCA_` / `GCF_` prefix stripped) → `predicted_*.genome`
  to look up ML-predicted phenotypes. Many CVM genomes have an empty
  `ncbi_accession` and therefore no entry in the predicted_* files.

## Examples

```bash
# closed genomes (contig_number == 1)
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_genome.csv.gz \
  | gunzip | awk -F, 'NR==1 || $3==1' | column -ts,
```

```bash
# get the FASTA for one strain
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_genome.csv.gz \
  | gunzip | awk -F, -v id=022 '$1==id {print $6}'
```

```bash
# high-quality assemblies only
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_genome.csv.gz \
  | gunzip | awk -F, 'NR==1 || $4 >= 95'
```
