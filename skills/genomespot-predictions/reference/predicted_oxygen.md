# predicted_oxygen.csv.gz

URL: `https://dt5rr68aivik7.cloudfront.net/downloads/predicted_oxygen.csv.gz`

GenomeSPOT-predicted oxygen tolerance, one row per genome.

## Columns

| Column | Description |
|---|---|
| `genome` | Numeric NCBI assembly accession (no `GCA_` / `GCF_` prefix and no version suffix). |
| `genome_version` | Full assembly accession including the `GCA_` prefix. |
| `optimum` | Predicted oxygen tolerance class — `tolerant` (aerobic / facultative) or `not tolerant` (obligate anaerobe). |
| `optimum_error` | Model uncertainty for the call. |
| `is_novel` | Boolean (`t`/`f`) — `t` if outside training distribution. |
| `confidence` | Coarse tier: `high`, `medium`, `low`. |

The schema differs from the temperature / pH / salinity files —
no `minimum` / `maximum` columns, since the prediction is a class
(tolerant / not tolerant) rather than a numeric range.

## Examples

```bash
# every confidently-anaerobic genome
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/predicted_oxygen.csv.gz \
  | gunzip | awk -F, 'NR==1 || ($3=="not tolerant" && $6=="high")' | column -ts,
```

```bash
# look up one genome
ACC=003675855
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/predicted_oxygen.csv.gz \
  | gunzip | awk -F, -v acc="$ACC" 'NR==1 || $1==acc'
```
