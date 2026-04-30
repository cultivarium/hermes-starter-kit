# cvm_mic90_raw_data.csv.gz

URL: `https://dt5rr68aivik7.cloudfront.net/downloads/cvm_mic90_raw_data.csv.gz`

Raw input to `cvm_mic_analysis.csv.gz` — one row per (strain × antibiotic
× medium × concentration × end timepoint), giving the OD reading
expressed as a fraction of the no-drug control.

## Columns

| Column | Description |
|---|---|
| `cvm` | Strain id. |
| `antibiotic` | Antibiotic name. |
| `concentration` | Concentration tested, in µg/ml. |
| `end_timepoint` | Time at which OD was read, in hours. |
| `media` | Medium long name. |
| `percent_of_max` | OD at this concentration / OD at zero antibiotic (the "max"). 1.0 = no inhibition; 0.0 = complete inhibition. The MIC90 in `cvm_mic_analysis` is the lowest concentration where this drops to ≤ 0.1. |

## When to use this vs. `cvm_mic_analysis`

- Use `cvm_mic_analysis` for MIC90 summaries and a yes/no resistance call.
- Use this raw file when you want to draw the dose-response curve, fit a
  Hill equation, or check the assay shape before trusting the MIC90.

## Examples

```bash
# the dose-response curve for a strain × antibiotic
CVM_ID=022
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_mic90_raw_data.csv.gz \
  | gunzip \
  | awk -F, -v id="$CVM_ID" 'NR==1 || ($1==id && $2=="Kanamycin")' \
  | (read -r header; printf '%s\n' "$header"; sort -t, -k3,3 -n) \
  | column -ts,
```
