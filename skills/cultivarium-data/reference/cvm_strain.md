# cvm_strain.csv.gz

URL: `https://dt5rr68aivik7.cloudfront.net/downloads/cvm_strain.csv.gz`

The strain master list. One row per non-archived CVM strain.

## Columns

| Column | Description |
|---|---|
| `cvm` | Cultivarium strain id (zero-padded, e.g. `022`, `086`, `129`). Join key for every other CVM-keyed file. |
| `catalog_number` | Vendor catalog number from the source repository (e.g. ATCC / DSMZ catalog id). |
| `species_id` | Numeric species id. Joins to `species.id` (`species.csv.gz`). |
| `strain_source` | The repository the strain was sourced from — `ATCC`, `DSMZ`, `BacDive`, etc. |

## Joins

- `species_id` → `species.id` for the species name and taxonomy classification.
- `cvm` is the foreign key in every other `cvm_*` file (`cvm_genome`,
  `cvm_ori_screen`, `cvm_media_screen`, `cvm_mic_analysis`,
  `cvm_mic90_raw_data`, `cvm_methylation_motif`, `cvm_methylation_gene`).
- `catalog_number` can be cross-referenced against `strain_id.csv.gz`
  (which carries `atcc`, `dsm`, `bacdive`, `ncbi`, `cvm` columns), but
  the join is by source-specific catalog id, not by a single key column.

## Examples

```bash
# how many strains, by source repository
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_strain.csv.gz \
  | gunzip | awk -F, 'NR>1 {print $4}' | sort | uniq -c | sort -rn
```

```bash
# strain count
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/cvm_strain.csv.gz \
  | gunzip | tail -n +2 | wc -l
```
