# predicted_temperature.csv.gz

URL: `https://dt5rr68aivik7.cloudfront.net/downloads/predicted_temperature.csv.gz`

GenomeSPOT-predicted growth temperature range, one row per genome. About
~16k rows.

## Columns

| Column | Description |
|---|---|
| `genome` | Numeric NCBI assembly accession (no `GCA_` / `GCF_` prefix and no version suffix). |
| `genome_version` | Full assembly accession including the `GCA_` prefix. |
| `optimum` | Predicted optimal growth temperature (°C). |
| `optimum_error` | Model uncertainty for the optimum (°C). |
| `minimum` | Predicted lower temperature bound for growth (°C). |
| `minimum_error` | Model uncertainty for the lower bound. |
| `maximum` | Predicted upper temperature bound for growth (°C). |
| `maximum_error` | Model uncertainty for the upper bound. |
| `is_novel` | Boolean (`t`/`f`) — `t` if the genome is outside the model's training distribution. Treat the prediction with extra caution. |
| `confidence` | Coarse tier: `high`, `medium`, `low`. |

## Examples

```bash
# thermophiles (predicted optimum >= 50 °C, high confidence)
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/predicted_temperature.csv.gz \
  | gunzip | awk -F, 'NR==1 || ($3 >= 50 && $10=="high")' | column -ts,
```

```bash
# psychrophiles (predicted optimum < 15 °C, high confidence)
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/predicted_temperature.csv.gz \
  | gunzip | awk -F, 'NR==1 || ($3 < 15 && $10=="high")' | column -ts,
```

```bash
# look up one genome
ACC=003675855
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/predicted_temperature.csv.gz \
  | gunzip | awk -F, -v acc="$ACC" 'NR==1 || $1==acc'
```
