# predicted_ph.csv.gz

URL: `https://dt5rr68aivik7.cloudfront.net/downloads/predicted_ph.csv.gz`

ML-predicted pH growth range per genome. Keyed by NCBI assembly
accession number, **not** by CVM id — see "Joining to a CVM strain"
below.

## Columns

| Column | Description |
|---|---|
| `genome` | Numeric NCBI assembly accession (no `GCA_` / `GCF_` prefix). |
| `genome_version` | Full assembly accession including the `GCA_` prefix. |
| `optimum` | Predicted optimal pH for growth. |
| `optimum_error` | Model uncertainty for the optimum. |
| `minimum` | Predicted lower pH bound for growth. |
| `minimum_error` | Model uncertainty for the lower bound. |
| `maximum` | Predicted upper pH bound for growth. |
| `maximum_error` | Model uncertainty for the upper bound. |
| `is_novel` | Boolean (`t`/`f`) — `t` if outside training distribution. |
| `confidence` | Coarse tier: `high`, `medium`, `low`. |

## Joining to a CVM strain

```bash
CVM_ID=022
ACC=$(curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_genome.csv.gz \
  | gunzip | awk -F, -v id="$CVM_ID" '$1==id {print $8}' | head -1)
NUM_ACC="${ACC#GC[AF]_}"
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/predicted_ph.csv.gz \
  | gunzip | awk -F, -v acc="$NUM_ACC" 'NR==1 || $1==acc'
```

CVM strains without an NCBI accession have no entry here.

## Examples

```bash
# every alkaliphile (predicted optimum > 9, high confidence)
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/predicted_ph.csv.gz \
  | gunzip | awk -F, 'NR==1 || ($3 > 9 && $10=="high")' | column -ts,
```
