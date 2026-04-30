# predicted_ph.csv.gz

URL: `https://dt5rr68aivik7.cloudfront.net/downloads/predicted_ph.csv.gz`

GenomeSPOT-predicted pH growth range, one row per genome.

## Columns

| Column | Description |
|---|---|
| `genome` | Numeric NCBI assembly accession (no `GCA_` / `GCF_` prefix and no version suffix). |
| `genome_version` | Full accession including the `GCA_` prefix. |
| `optimum` | Predicted optimal pH for growth. |
| `optimum_error` | Model uncertainty for the optimum. |
| `minimum` | Predicted lower pH bound for growth. |
| `minimum_error` | Model uncertainty for the lower bound. |
| `maximum` | Predicted upper pH bound for growth. |
| `maximum_error` | Model uncertainty for the upper bound. |
| `is_novel` | Boolean (`t`/`f`) — `t` if outside training distribution. |
| `confidence` | Coarse tier: `high`, `medium`, `low`. |

## Examples

```bash
# alkaliphiles (predicted optimum > 9, high confidence)
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/predicted_ph.csv.gz \
  | gunzip | awk -F, 'NR==1 || ($3 > 9 && $10=="high")' | column -ts,
```

```bash
# acidophiles (predicted optimum < 5, high confidence)
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/predicted_ph.csv.gz \
  | gunzip | awk -F, 'NR==1 || ($3 < 5 && $10=="high")' | column -ts,
```
