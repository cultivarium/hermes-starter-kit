# cvm_mic_analysis.csv.gz

URL: `https://dt5rr68aivik7.cloudfront.net/downloads/cvm_mic_analysis.csv.gz`

Per-(strain × antibiotic × medium × temperature) MIC summary, derived
from the raw concentration series in `cvm_mic90_raw_data.csv.gz`.
MIC90 is reported as the lowest tested concentration that suppresses
growth to ≤ 10% of the maximum.

## Columns

| Column | Description |
|---|---|
| `cvm` | Strain id. |
| `antibiotic` | Antibiotic name (e.g. `Kanamycin`, `Chloramphenicol`, `Erythromycin`). |
| `end_timepoint` | Time at which OD was read for the analysis, in hours. |
| `fold_change` | Maximum / minimum OD ratio observed in the series — proxy for assay dynamic range. |
| `maximum_concentration` | Highest concentration tested, in µg/ml. |
| `media` | Medium used for the assay (long name). |
| `mic90` | Concentration at which growth is reduced to ≤ 10% of max, in µg/ml. Empty if growth is never suppressed within the tested range. |
| `resistant` | Boolean (`t`/`f`) — `t` when no MIC90 could be determined within the tested range (i.e. strain is resistant). |
| `temperature` | Incubation temperature in °C. |

## Notes

- An empty `mic90` together with `resistant = t` means the strain
  tolerated every concentration tested. To estimate a lower bound on
  the true MIC, use `maximum_concentration`.
- `mic90` is medium- and temperature-dependent — always report
  alongside its `media` and `temperature` columns.

## Examples

```bash
# every antibiotic susceptibility row for one strain
CVM_ID=022
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_mic_analysis.csv.gz \
  | gunzip | awk -F, -v id="$CVM_ID" 'NR==1 || $1==id' | column -ts,
```

```bash
# every strain resistant to kanamycin
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_mic_analysis.csv.gz \
  | gunzip | awk -F, 'NR==1 || ($2=="Kanamycin" && $8=="t")' | column -ts,
```
