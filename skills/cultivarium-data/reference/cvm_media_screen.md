# cvm_media_screen.csv.gz

URL: `https://dt5rr68aivik7.cloudfront.net/downloads/cvm_media_screen.csv.gz`

Growth / media screen results — strain × medium × temperature combinations
with growth kinetics derived from microplate OD600 traces. Each row is
one screen condition aggregated over replicate wells.

## Columns

| Column | Description |
|---|---|
| `cvm` | Strain id. |
| `media` | Medium long name (`LB`, `R2A`, `Marine Broth 2216`, etc.) — already resolved from the internal media id. |
| `temperature` | Incubation temperature in °C. |
| `endpoint` | Time at which the curve was evaluated, in hours. |
| `wells` | Number of replicate wells in the assay. |
| `is_growing` | Boolean (`t`/`f`) — whether growth was detected. |
| `auc_avg` | Mean area under the OD curve across replicates. |
| `auc_std_dev` | Standard deviation of AUC. |
| `auc_reps` | Number of replicates with a usable AUC. |
| `max_od_avg` | Mean maximum OD600 reached. |
| `max_od_std_dev` | Standard deviation of max OD. |
| `max_od_reps` | Number of replicates with a usable max OD. |
| `doubling_time_avg` | Mean doubling time during exponential phase, in hours. Empty when not in growth phase. |
| `doubling_time_std_dev` | Standard deviation of doubling time. |
| `doubling_time_reps` | Number of replicates with a usable doubling time. |
| `time_to_od_02_avg` | Mean time to reach OD600 = 0.2, in hours. |
| `time_to_od_02_std_dev` | Standard deviation of time-to-OD-0.2. |
| `time_to_od_02_reps` | Number of replicates with a usable time-to-OD-0.2. |
| `n` | Total number of replicate measurements feeding the row (≥ each `*_reps` count). |

## Notes

- A row with `is_growing = f` is an explicit "tested, did not grow" — distinct
  from a strain × medium that simply never appears in the file ("not tested").
- The metric replicate counts (`auc_reps`, `max_od_reps`, etc.) can be lower
  than `n` when some wells failed QC for a specific metric.

## Examples

```bash
# every medium one strain grows in
CVM_ID=022
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_media_screen.csv.gz \
  | gunzip | awk -F, -v id="$CVM_ID" 'NR==1 || ($1==id && $6=="t")' | column -ts,
```

```bash
# fastest-growing strain × medium combos (lowest doubling time)
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_media_screen.csv.gz \
  | gunzip | awk -F, 'NR==1 || $13!=""' \
  | (read -r header; printf '%s\n' "$header"; sort -t, -k13,13 -n) \
  | head -20 | column -ts,
```
