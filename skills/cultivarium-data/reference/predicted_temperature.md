# predicted_temperature.csv.gz

URL: `https://dt5rr68aivik7.cloudfront.net/downloads/predicted_temperature.csv.gz`

ML-predicted temperature growth range per genome. Keyed by NCBI
assembly accession number, **not** by CVM id.

## Columns

| Column | Description |
|---|---|
| `genome` | Numeric NCBI assembly accession (no `GCA_` / `GCF_` prefix). |
| `genome_version` | Full accession including the `GCA_` prefix. |
| `optimum` | Predicted optimal growth temperature (°C). |
| `optimum_error` | Model uncertainty for the optimum. |
| `minimum` | Predicted lower temperature bound for growth (°C). |
| `minimum_error` | Model uncertainty for the lower bound. |
| `maximum` | Predicted upper temperature bound for growth (°C). |
| `maximum_error` | Model uncertainty for the upper bound. |
| `is_novel` | Boolean (`t`/`f`) — `t` if outside training distribution. |
| `confidence` | Coarse tier: `high`, `medium`, `low`. |

## Joining to a CVM strain

```bash
CVM_ID=022
ACC=$(curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_genome.csv.gz \
  | gunzip | awk -F, -v id="$CVM_ID" '$1==id {print $8}' | head -1)
NUM_ACC="${ACC#GC[AF]_}"
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/predicted_temperature.csv.gz \
  | gunzip | awk -F, -v acc="$NUM_ACC" 'NR==1 || $1==acc'
```

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
