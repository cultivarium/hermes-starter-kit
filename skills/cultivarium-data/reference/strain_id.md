# strain_id.csv.gz

URL: `https://dt5rr68aivik7.cloudfront.net/downloads/strain_id.csv.gz`

Cross-reference table mapping a strain across the major public catalogs.
This file is **not** Cultivarium-specific — it indexes strains across
ATCC, DSM (DSMZ), BacDive, NCBI, and Cultivarium's own `cvm` ids,
including strains the lab does not currently hold.

Use it to translate one catalog id into another, or to look up a strain
by any of its public identifiers.

## Columns

| Column | Description |
|---|---|
| `id` | Internal record id (often the catalog id of the source repository, e.g. a BacDive id). |
| `species_id` | Numeric species id. Joins to `species.id`. |
| `name` | Canonical strain name including designation (e.g. `Acetobacter aceti NCIB 8621`). |
| `strain_designation` | The strain designation portion of the name (e.g. `NCIB 8621`). |
| `atcc` | ATCC catalog number, when known. |
| `bacdive` | BacDive id, when known. |
| `cvm` | Cultivarium `cvm` id, when the strain is in CVM's collection. |
| `dsm` | DSMZ catalog number, when known. |
| `ncbi` | NCBI Taxonomy id, when known. |
| `cultivarium_defined` | Boolean (`t`/`f`) — `t` if the row was created or curated by Cultivarium rather than imported from a source database. |

## Notes

- Many rows have `cvm` empty — those are strains documented in public
  catalogs that the lab does not hold.
- A strain may appear with multiple repository ids on the same row; the
  table is "best-effort merged" rather than one-row-per-source.
- `species_id` joins to the same `species.csv.gz` table that
  `cvm_strain.species_id` joins to.

## Examples

```bash
# look up CVM022 across catalogs
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/strain_id.csv.gz \
  | gunzip | awk -F, 'NR==1 || $7=="022"' | column -ts,
```

```bash
# find a strain by ATCC number
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/strain_id.csv.gz \
  | gunzip | awk -F, 'NR==1 || $5=="44963"' | column -ts,
```
