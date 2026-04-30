# species.csv.gz

URL: `https://dt5rr68aivik7.cloudfront.net/downloads/species.csv.gz`

Species lookup table. The `id` column is the join target for the
`species_id` columns in `cvm_strain.csv.gz` and `strain_id.csv.gz`.
Indexes ~all species the lab has ever recorded a strain for, including
those in the broader public catalogs (much larger than the CVM
collection).

## Columns

| Column | Description |
|---|---|
| `id` | Numeric species id. |
| `name` | Species name (`Genus species` form, occasionally `Genus sp. <designation>`). |
| `classification` | High-level domain — `Bacteria`, `Archaea`, `Fungi`, `Eukaryota`. |
| `synonyms` | Postgres-array notation listing alternative names, e.g. `{"Microcyclus aquaticus"}`. May be empty. |

## Examples

```bash
# look up species by id
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/species.csv.gz \
  | gunzip | awk -F, 'NR==1 || $1==363277'
```

```bash
# every species name matching a regex
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/species.csv.gz \
  | gunzip | awk -F, 'NR==1 || $2 ~ /Bacillus subtilis/' | column -ts,
```

```bash
# how many species in each domain
curl -s https://dt5rr68aivik7.cloudfront.net/downloads/species.csv.gz \
  | gunzip | awk -F, 'NR>1 {print $3}' | sort | uniq -c | sort -rn
```
