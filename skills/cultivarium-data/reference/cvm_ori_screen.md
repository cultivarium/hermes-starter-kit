# cvm_ori_screen.csv.gz

URL: `https://dt5rr68aivik7.cloudfront.net/downloads/cvm_ori_screen.csv.gz`

Results of Cultivarium's plasmid origin-of-replication (ORI) screen.
Each row is one (strain × ORI × delivery condition) combination that
went through NGS-quantified maintenance assay. The screen delivers a
library of ORI-bearing plasmids alongside a dummy control; fold
enrichment is the NGS read count of the ORI relative to the dummy.

## Columns

| Column | Description |
|---|---|
| `cvm` | Recipient strain id. |
| `ori_name` | ORI name as users refer to it — `pBBR1`, `RSF1010`, `pSC101ts`, `pRO1614`, etc. (the `_ori` / ` ORI` suffix has been stripped). |
| `conjugation_medium` | Medium used during conjugation (donor → recipient mating step). |
| `selective_medium` | Medium used to select transconjugants after delivery. |
| `antibiotic` | Selection antibiotic used during the screen. |
| `antibiotic_concentrations` | Set notation, e.g. `{0.25}` or `{2.5,5}` — concentrations tested in µg/ml. |
| `transconjugants_obtained` | Boolean — `t` if any colonies were recovered, `f` otherwise. Conjugation can fail before NGS quantification. |
| `conjugation_score` | Numeric conjugation efficiency proxy when colonies were obtained; empty otherwise. |
| `fold_enrichment_avg` | Mean fold enrichment of this ORI vs. dummy across replicates. |
| `fold_enrichment_std_dev` | Standard deviation of fold enrichment across replicates. |
| `n` | Number of replicates contributing to the average. |
| `confidence` | Tier derived from `fold_enrichment_avg` (see table below). May be empty when the run failed before NGS. |

## Confidence tiers

| Tier | Fold enrichment | Interpretation |
|---|---|---|
| `high` | ≥ 1000× | ORI is robustly maintained |
| `medium` | 100 – 999× | Functional but variable |
| `low` | 10 – 99× | Weak maintenance |
| `non-functional` | < 10× | Not maintained |

A row with empty `confidence` and `fold_enrichment_avg` means the
delivery step failed (no transconjugants), so the ORI was never
quantified — not that it was tested and found non-functional.

## Examples

```bash
# every functional ORI for one strain, sorted by enrichment
CVM_ID=061
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_ori_screen.csv.gz \
  | gunzip \
  | awk -F, -v id="$CVM_ID" 'NR==1 || ($1==id && $12!="")' \
  | (read -r header; printf '%s\n' "$header"; sort -t, -k10,10 -rn) \
  | column -ts,
```

```bash
# every strain in which pBBR1 is high-confidence
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_ori_screen.csv.gz \
  | gunzip \
  | awk -F, 'NR==1 || ($2=="pBBR1" && $12=="high")' | column -ts,
```

```bash
# list of all ORIs ever tested
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_ori_screen.csv.gz \
  | gunzip | awk -F, 'NR>1 {print $2}' | sort -u
```
