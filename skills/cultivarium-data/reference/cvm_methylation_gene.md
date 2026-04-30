# cvm_methylation_gene.csv.gz

URL: `https://dt5rr68aivik7.cloudfront.net/downloads/cvm_methylation_gene.csv.gz`

Restriction-modification (RM) gene annotations per CVM strain, derived
from MicrobeMod-style HMM scanning and REBASE homology lookup. Each
row is one annotated gene.

## Columns

| Column | Description |
|---|---|
| `cvm` | Strain id. |
| `operon` | Operon identifier the gene belongs to (groups together genes in the same RM system). |
| `gene` | Gene name / locus tag from the genome annotation. |
| `system_type` | RM system class: `Type I`, `Type II`, `Type III`, or `Type IV`. |
| `gene_type` | Functional role within the system — `M` (methyltransferase), `R` (restriction enzyme), `S` (specificity subunit). |
| `hmm` | HMM model that matched (the underlying RM system family). |
| `e_value` | HMM hit e-value — lower is more confident. |
| `rebase_homolog` | Closest REBASE database entry, when one was found. |
| `homolog_identity` | Percent amino-acid identity to the REBASE homolog. |
| `homolog_methylation` | Methylation type produced by the REBASE homolog (`4mC` / `5mC` / `6mA`), when annotated. |
| `homolog_motif` | Motif recognized by the REBASE homolog, when annotated. Use this to associate a gene with a row in `cvm_methylation_motif.csv.gz`. |

## Notes

- Multiple genes can share an `operon` — Type I systems are typically
  encoded as `M-S-R` operons, so expect three rows per Type I system.
- An empty `rebase_homolog` means no significant REBASE hit was found;
  the HMM gave the system-type call but the recognition motif is unknown.

## Examples

```bash
# the RM systems annotated in one strain
CVM_ID=022
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_methylation_gene.csv.gz \
  | gunzip | awk -F, -v id="$CVM_ID" 'NR==1 || $1==id' | column -ts,
```

```bash
# all Type IV (modification-dependent) restriction enzymes
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_methylation_gene.csv.gz \
  | gunzip | awk -F, 'NR==1 || $4=="Type IV"' | column -ts,
```
