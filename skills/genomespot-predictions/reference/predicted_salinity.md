# predicted_salinity.csv.gz

URL: `https://dt5rr68aivik7.cloudfront.net/downloads/predicted_salinity.csv.gz`

GenomeSPOT-predicted NaCl tolerance range, one row per genome.

## Columns

| Column | Description |
|---|---|
| `genome` | Numeric NCBI assembly accession (no `GCA_` / `GCF_` prefix and no version suffix). |
| `genome_version` | Full accession including the `GCA_` prefix. |
| `optimum` | Predicted optimal NaCl concentration for growth (% w/v). |
| `optimum_error` | Model uncertainty for the optimum. |
| `minimum` | Predicted lower NaCl bound for growth. |
| `minimum_error` | Model uncertainty for the lower bound. |
| `maximum` | Predicted upper NaCl bound for growth. |
| `maximum_error` | Model uncertainty for the upper bound. |
| `is_novel` | Boolean (`t`/`f`) — `t` if outside training distribution. |
| `confidence` | Coarse tier: `high`, `medium`, `low`. |

## Examples

```bash
# halophiles (predicted optimum > 5 %, high confidence)
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/predicted_salinity.csv.gz \
  | gunzip | awk -F, 'NR==1 || ($3 > 5 && $10=="high")' | column -ts,
```

```bash
# strict freshwater organisms (predicted optimum < 0.5 %, high confidence)
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/predicted_salinity.csv.gz \
  | gunzip | awk -F, 'NR==1 || ($3 < 0.5 && $10=="high")' | column -ts,
```
