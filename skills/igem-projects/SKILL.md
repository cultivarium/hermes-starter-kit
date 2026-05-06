---
name: igem-projects
description: Search and answer questions about past iGEM (International Genetically Engineered Machine) competition projects from 2004 to 2025 — covering ~4,900 projects across ~2,000 teams. Use whenever a user asks about iGEM teams, prior iGEM projects, project ideas that have already been done, what won medals or prizes, projects on a specific topic (phage therapy, biosensors, bioremediation, etc.), projects in a specific organism or village, or trends in iGEM (regions, sections, topics over time). Also use this when an iGEM team is scoping a new project and wants prior-art screening, or when a mentor/judge wants to look up a team's history. Includes project metadata and provides wiki links for deeper investigation when needed.
---

# iGEM Projects

A query interface over a snapshot of the iGEM project registry covering 2004–2025 (4,873 projects, 1,984 distinct team names). The data ends at the close of the 2025 cycle.

The data source lives in `data/igem_projects.csv` and is queried via `scripts/query.py`.

## When to use this skill

Use whenever the user asks anything about iGEM as a competition or its past projects. Common shapes:

- *"Has anyone done an iGEM project on X?"* → keyword search title + description
- *"Show me Gold-medal Therapeutics projects from 2023"* → multi-filter
- *"What projects has [team] done?"* → team filter
- *"Which iGEM teams have used Vibrio natriegens?"* → organism keyword search
- *"What kinds of projects win Grand Prize?"* → prize filter, then analyze
- *"How has High School participation grown over time?"* → aggregation
- *"We want to do a CRISPR-based diagnostic — what prior art exists?"* → prior-art screening for a new team

## How to query

Always use the bundled script — do not re-parse the data source inline. The script handles schema quirks (BOM, trailing empty columns, section casing inconsistencies) and provides specialized modes for organism queries.

```bash
cd <skill-path> && python -m scripts.query [filters]
```

The script writes warnings to stderr when a filter value doesn't appear in the data (e.g. `--medal Platinum`, `--year 2099`). If you see a stderr warning, treat the zero result as "filter typo" rather than "no real matches."

### Filter flags

| Flag | What it does |
|---|---|
| `--keyword "phage therapy"` | Substring in Project_Title + Project_Description. Repeat for AND. |
| `--any-keyword "phage" --any-keyword "bacteriophage"` | OR-group: at least one must match. Repeat for OR. Use for synonym broadening. Combines with `--keyword` as `(all --keyword AND) AND (any --any-keyword OR)`. |
| `--year 2023` / `--year-min 2020` / `--year-max 2024` | Year filters |
| `--team "Foshan"` | Substring in team name |
| `--medal Gold` | Gold / Silver / Bronze |
| `--village Therapeutics` | Substring on Village (single value, current label only) |
| `--village-family environment` | Group of related villages spanning iGEM's renames. Values: `environment`, `manufacturing`, `health`, `software`, `food`. **Use this for cross-year thematic queries** — see "Village renames" caveat below. |
| `--section "High School"` | Or `--section college` to include Undergrad+Overgrad+Collegiate (case-insensitive — handles 2025's lowercase `undergrad` rows) |
| `--region Asia` / `--country China` | Geography |
| `--species "E. coli"` | Substring on Species column. Usually keyword search of title/description is broader and better — see "Organism queries" below. |
| `--prize "Best Wiki"` | Substring on Prizes column. Caution: short substrings like "Best" hit dozens of distinct prizes — use the full prize name. |
| `--count-only` | Just the count |
| `--max-rows 50` | Default 25 |
| `--columns Year,Team,Project_Title,Wiki_Link` | Pick which columns to show |
| `--json` | JSON output instead of TSV (full descriptions, no truncation) |

Default sort is year descending, then team alphabetical.

### Synonym broadening — when keyword search misses things

iGEM projects vary wildly in how they describe themselves. A search for `--keyword "phage therapy"` will match "phage therapy" and nothing else, missing "phage-based therapeutics," "bacteriophage treatment," and so on. Substring matching is also literal — `--keyword "Bacillus subtilis"` misses "B. subtilis" (with the period).

**Default behavior**: when running a topic search, think about what synonyms or near-synonyms a project might use, and pass them as an OR-group via `--any-keyword`. If the user's term has both a common name and a Latin name, an abbreviation, or a related term (mechanism, application, alternative phrasing), include them all.

Examples of when to broaden:

| User asks about | Pass as `--any-keyword` |
|---|---|
| phage therapy | "phage therapy", "bacteriophage", "phage-based" |
| biosensor | "biosensor", "biosensing", "detection" |
| bioplastic | "bioplastic", "PHA", "polyhydroxyalkanoate", "PLA" |
| CRISPR diagnostic | "CRISPR diagnostic", "Cas12", "Cas13", "SHERLOCK", "DETECTR" |
| heavy metal cleanup | "heavy metal", "lead", "arsenic", "cadmium", "mercury", "bioremediation" |
| Bacillus subtilis | "Bacillus subtilis", "B. subtilis", "B.subtilis" |

When you broaden, tell the user which synonyms you searched so they can suggest others.

### Organism queries

For organism queries, **default to `--any-keyword` with abbreviation variants** (e.g. "Bacillus subtilis", "B. subtilis"). The Species column is only ~48% filled, but in practice almost everything tagged in Species also appears in the title or description, so a thoughtful keyword search captures effectively the full set.

(An earlier version of this skill recommended a `--species-merge` flag for the Species ∪ keyword union. That flag has been removed because empirical testing showed it added 0–15 rows out of hundreds for common organisms — the Species column is essentially a subset of what keyword search finds. Use `--any-keyword` with name variants instead.)

Always state the result is a **lower bound** — a project might use *V. natriegens* without naming it in the title, description, or species tag.

### Aggregations and trends

The script handles single queries; multi-query aggregations (counts by year, top villages, distribution by region) require dropping into Python directly. The `load_rows()` helper does the parsing for you — use it instead of re-implementing the data loading.

```python
import sys
sys.path.insert(0, '<skill-path>/scripts')
from query import load_rows
from collections import Counter

rows = load_rows()
# Example: High School project count by year
hs = [r for r in rows if r.get('Section') == 'High School']
by_year = Counter(r['Year'] for r in hs)
for y in sorted(by_year):
    print(y, by_year[y])
```

Common aggregation patterns to reach for:
- Project counts grouped by Year, Section, Village, Region, or Country
- Topic share over time (filter by keyword, then count by year)
- Medal distribution within a slice (e.g., medals among phage-therapy projects)
- Prize patterns — which villages produce the most Grand Prize winners, etc.

When reporting trends, always sanity-check against the per-year totals (some years are larger than others) and report **percentages**, not just raw counts.

When grouping by Section across years, lowercase the value before comparison — 2025 uses lowercase `'undergrad'` while earlier years use capitalized `'Undergrad'`. The CLI flag `--section` already handles this case-insensitively, but Python aggregations do not unless you add `.lower()`.

## Schema and important caveats

The data has these columns:

`Team Year, Team, Year, Wiki_Link, Project_Title, Project_Description, Species, Village, Section, Region, Country, Medal, Prizes, Nominations`

Caveats that materially affect answers — always factor these in and tell the user when they apply:

1. **Species is only ~48% filled.** Querying the Species column alone misses roughly half the corpus. **In practice, keyword search of title/description finds nearly everything Species tags** plus a lot more — so prefer `--any-keyword` with name variants over `--species`. Even then, treat the result as a lower bound: a project might use an organism without naming it in the searchable text. State this explicitly when reporting organism counts.
2. **Section labels overlap across eras.** "Collegiate" (older, pre-~2022), "Undergrad", and "Overgrad" all describe college-level teams. iGEM split Collegiate into Undergrad/Overgrad around 2022. For "college-level" queries pass `--section college` (the script collapses all variants). Don't treat Collegiate vs. Undergrad as a meaningful distinction.
3. **2025 uses lowercase `'undergrad'`** for Section while earlier years use capitalized `'Undergrad'`. The CLI handles this; Python aggregations do not unless you `.lower()` the value before grouping.
4. **Medal field is ~86% filled.** The blanks are mostly projects that didn't qualify for a medal (or older years with different judging). Don't equate "blank" with "Bronze."
5. **Prizes and Nominations are sparse** (~9% and ~19%) — only filled for projects that actually won/were nominated. This is correct, not missing data.
6. **Wiki_Link is 100% filled** in this snapshot. Every project has a wiki link.
7. **Village taxonomy has been heavily renamed over time** — a Therapeutics-vs-Environment comparison for recent years will go badly wrong if you treat current village labels as continuous with historical ones. The script provides `--village-family` to handle the most common rename groups (`environment`, `manufacturing`, `health`, `software`, `food`) — use that for cross-year thematic queries. The concrete renames/splits in the data:
   - **Environment** (2007–2023, 621 projects) was split into **Bioremediation** (2023–), **Climate Crisis** (2022–), **Conservation** (2022–), and partly **Agriculture** (2023–). `--village-family environment` unions all five.
   - **Manufacturing** (2009–2022, 265) was renamed to **Biomanufacturing** (2023–). `--village-family manufacturing`.
   - **Health & Medicine** (2010–2015, 197) was split into **Therapeutics**, **Diagnostics**, **Oncology**, and **Infectious Diseases**. `--village-family health`.
   - **Information Processing** (2007–2020, 112) and **Software** (2014–2021, 60) were folded into **Software & AI** (2022–). `--village-family software`.
   - **High School** as a village label (2015–2023, 594) was retired — 2024+ HS teams use topical villages and are identified via Section instead.
   - Several short-lived villages exist (Hardware, Measurement, Microfluidics, Community Labs, Open) — don't read significance into their disappearance.
   For thematic queries that span the rename boundaries, prefer `--village-family` or keyword search over `--village`.
8. **Project_Title may contain HTML entities** (e.g., `&#65306;` for a fullwidth colon, `&#934;` for the Greek letter Phi) and italic markup (e.g., `<i>B. subtilis</i>`). Strip or render these when summarizing for the user.
9. **2025 row count is ~413** — comparable to 2024 (389) and 2023 (391). Treat 2025 as a complete year for trend analysis.
10. **Year totals vary widely** — 2004 has 5 rows, 2012 jumps to 217, 2018+ averages ~330. When reporting year-over-year trends, always normalize to percentages.
11. **Project_Title and Project_Description are ~94% filled** — most blanks are in 2004–2007 (a few hundred early-year stubs) plus scattered cases in later years. Keyword search on title/description will systematically miss these — for very old years lean on the wiki link instead.

## Wiki fetching — confirm first

Project_Description is a single paragraph. The wiki has the actual science (parts, constructs, protocols, results). When the user's question requires wiki-level detail — specific BioBricks/parts used, plasmid backbones, transformation protocols, characterization data, modeling approaches, hardware, software, human practices specifics — **do not auto-fetch**. Instead:

1. Run the query to narrow to candidate projects.
2. Show the candidates with their Wiki_Link values.
3. Ask the user which one(s) to fetch into context, or if they want all of them.
4. Only after explicit confirmation, run `web_search` for the team name + project title (e.g. "SDU-Denmark 2021 PsiloAid psilocybin"), then `web_fetch` on the resulting URLs.

**Important**: `web_fetch` is permissions-gated and may refuse URLs that come straight from the data file. Always run `web_search` first to surface the same URLs through search results — that's what unlocks them for fetching. The search results often also return useful snippet content directly, sometimes enough to answer the question without a full fetch. Older iGEM wikis (`https://YEAR.igem.org/Team:NAME` for 2004–2022) may also have multi-page structure (Description, Results, Experiments, Parts, Safety, etc.) — search for the specific subpage you need rather than landing only on the team home page.

This rule exists because wiki fetches are slow and the user may already see what they need from the title and description.

If the user's question is clearly answerable from project metadata alone (counts, lists, medal stats, geography), don't even mention fetching.

## Default output format

For "find projects on X"-shaped queries, return both:

1. **A short prose summary** — total count, notable patterns (era, region, medal distribution, recurring themes), any caveats from the list above that apply, and the synonyms searched.
2. **A table of matches**, with Year, Team, Project_Title, Village, Country, Medal, Wiki_Link as the default columns. Cap at ~15–25 rows in chat; offer to dump the full set as a downloadable file if there are more.

For pure aggregate questions ("how many", "top 5", "trend over time"), prose with a small summary table is fine — no need for the full table-of-matches.

## Worked examples

**Example 1 — keyword search with synonym broadening**
User: *"Have any iGEM teams worked on phage therapy?"*

A literal phrase search would miss many projects. Broaden up front:
```bash
python -m scripts.query --any-keyword "phage therapy" --any-keyword "bacteriophage" --any-keyword "phage-based"
```
Summarize: total count, year range, regional spread, medal distribution. Tell the user which terms you searched. Show the table. Don't fetch wikis unless asked.

**Example 2 — prior-art for a new team (multi-concept topic)**
User: *"Our team wants to engineer cyanobacteria to produce bioplastics. What prior iGEM work exists?"*

This needs an AND across two concepts, with each concept broadened:
```bash
python -m scripts.query --keyword "cyanobacteria" --any-keyword "bioplastic" --any-keyword "PHA" --any-keyword "polyhydroxyalkanoate"
```
If results are thin, drop the AND and run a broader OR sweep:
```bash
python -m scripts.query --any-keyword "cyanobacteria" --any-keyword "Synechocystis" --any-keyword "Synechococcus" --year-min 2018
```
Summarize what's been done, flag the closest matches, offer to fetch their wikis for construct details.

**Example 3 — team history with disambiguation**
User: *"What's MIT's iGEM track record?"*

```bash
python -m scripts.query --team "MIT" --columns Year,Team,Project_Title,Village,Medal,Prizes,Wiki_Link
```
**Always inspect the distinct team names** in the result before reporting — `--team` is a substring match and routinely conflates separate institutions. A search for "MIT" returns rows for MIT (Cambridge), MIT_MAHE / MIT-MAHE (Manipal Academy of Higher Education, India — note the hyphen vs. underscore variation iGEM has used inconsistently), MITADTBIO_Pune (MIT-ADT University, India), MITWPU-BHARAT, RMIT_Australia (Royal Melbourne Institute of Technology), MIT_E (a sub-team designation), and even false positives like Shasta_Summit_CA and Summit City Bio where "mit" lives inside another word.

When this happens, group the results by exact team name and present them as a disambiguation table to the user before answering the original question. Also note that the same school may appear under inconsistent name variants across years (`MIT_MAHE` vs `MIT-MAHE`, `Foshan-GreatBay_A` vs `Foshan-GreatBay_SCIE`) — treat these as the same team.

**Example 4 — organism lookup**
User: *"Which teams have used Vibrio natriegens?"*

Use `--any-keyword` with abbreviation variants. Keyword search of title + description finds nearly everything the Species column tags, plus more.
```bash
python -m scripts.query --any-keyword "natriegens" --any-keyword "V. natriegens" --any-keyword "Vibrio natriegens"
```
Tell the user: "This is a lower bound — a project might use *V. natriegens* without naming it in the title or description."

**Example 5 — aggregate trend**
User: *"How has High School participation in iGEM changed over time?"*

This is an aggregation — drop into Python:
```python
import sys
sys.path.insert(0, '<skill-path>/scripts')
from query import load_rows
from collections import Counter

rows = load_rows()
hs = [r for r in rows if r.get('Section') == 'High School']
by_year = Counter(r['Year'] for r in hs)
total_by_year = Counter(r['Year'] for r in rows)

for y in sorted(by_year):
    pct = 100 * by_year[y] / total_by_year[y]
    print(f"{y}: {by_year[y]} HS projects ({pct:.1f}% of all projects)")
```
Report both raw counts and percentages. Note that ~two-thirds of HS projects are tagged with the village "High School" (the iGEM track) rather than a topical village — so any further "what topics do HS teams work on" question needs to be answered using the subset that has a topical village.

**Example 6 — cross-rename village trend**
User: *"Has interest in environmental projects in iGEM grown or shrunk over the past 5 years?"*

`--village Environment` would say "shrunk to zero by 2024" — wrong, because Environment was renamed/split. Use `--village-family environment`:
```bash
python -m scripts.query --village-family environment --year-min 2020 --count-only
# Then drop into Python for the per-year breakdown:
```
```python
import sys
sys.path.insert(0, '<skill-path>/scripts')
from query import load_rows, VILLAGE_FAMILIES
from collections import Counter

rows = load_rows()
env_family = VILLAGE_FAMILIES['environment']
fam = [r for r in rows if r.get('Village','').lower() in env_family]
total_by_year = Counter(r['Year'] for r in rows)
fam_by_year = Counter(r['Year'] for r in fam)
for y in sorted(fam_by_year):
    if int(y) >= 2020:
        pct = 100 * fam_by_year[y] / total_by_year[y]
        print(f"{y}: {fam_by_year[y]} ({pct:.1f}% of all)")
```
Reports the actual trend (growing in absolute terms, ~22–28% of all projects across 2020–2025) and explicitly tells the user which historical and current village labels you grouped together.

## Output integrity

- Never invent project titles, teams, or years not present in the data.
- **When a query returns zero matches**: first check whether the script wrote a stderr warning (filter-value typo). If not, broaden once with synonyms or a less specific term before reporting "no projects." If the broadened query also returns zero, say so directly rather than padding with adjacent-but-different work. If broadening surfaces adjacent work (e.g., a search for a very specific subterm returns zero, but the parent topic returns several projects on adjacent applications), present the adjacent work clearly labeled as adjacent, not as a match. Don't conflate "zero on the specific topic" with "zero in the area."
- Year range in the data is 2004–2025; reject or flag queries outside that range.
- Render HTML entities and italic tags from titles/descriptions (e.g., `<i>B. subtilis</i>` → *B. subtilis*) when summarizing for the user.

## Maintenance

When `data/igem_projects.csv` is refreshed (typically annually as iGEM closes a new season), the numbers cited throughout this file — total rows, distinct teams, fill rates, year totals, the latest-year row count in caveat #9 — will drift. Run `python -m scripts.data_stats` to print the updated values, then paste them into:

- The intro line ("4,873 projects, 1,984 distinct team names")
- Caveat #1 (Species fill %), #4 (Medal fill %), #5 (Prizes/Nominations %), #6 (Wiki_Link %), #9 (latest-year row count and comparison to prior years), #11 (Title/Description fill %)
- The village rename map in caveat #7 if any new village names appear or old ones disappear

`data_stats.py` also runs sanity checks: it flags Section casing drift (e.g. "undergrad" vs "Undergrad" — relevant to caveat #3), reports the college-collapse total, and lists villages not seen in the latest year. If a new village appears that doesn't fit an existing family in `VILLAGE_FAMILIES`, consider adding it to `scripts/query.py`.
