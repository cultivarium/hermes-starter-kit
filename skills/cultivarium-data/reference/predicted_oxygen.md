# predicted_oxygen.csv.gz

URL: `https://dt5rr68aivik7.cloudfront.net/downloads/predicted_oxygen.csv.gz`

ML-predicted oxygen tolerance per genome. The `genome` column is an
**NCBI assembly accession number** (the numeric suffix of `GCA_<n>` /
`GCF_<n>`), not a CVM id. Predictions cover both Cultivarium-sequenced
genomes (when an NCBI accession exists) and a broader set of public
reference genomes.

## Columns

| Column | Description |
|---|---|
| `genome` | Numeric NCBI assembly accession (no `GCA_` / `GCF_` prefix). |
| `genome_version` | Full assembly accession including the `GCA_` prefix. |
| `optimum` | Predicted oxygen tolerance class — `tolerant` (aerobic / facultative) or `not tolerant` (obligate anaerobe). |
| `optimum_error` | Model uncertainty estimate for the call. |
| `is_novel` | Boolean (`t`/`f`) — `t` if the genome is outside the model's training distribution. |
| `confidence` | Coarse confidence tier: `high`, `medium`, `low`. |

## Joining to a CVM strain

```bash
CVM_ID=022
ACC=$(curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_genome.csv.gz \
  | gunzip | awk -F, -v id="$CVM_ID" '$1==id {print $8}' | head -1)
NUM_ACC="${ACC#GC[AF]_}"
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/predicted_oxygen.csv.gz \
  | gunzip | awk -F, -v acc="$NUM_ACC" 'NR==1 || $1==acc'
```

When a CVM strain has no NCBI accession in `cvm_genome`, the prediction
is not available in this dataset.

## Examples

```bash
# every confidently-anaerobic genome
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/predicted_oxygen.csv.gz \
  | gunzip | awk -F, 'NR==1 || ($3=="not tolerant" && $6=="high")' | column -ts,
```
