---
name: igem-past-winners
description: >
  Look up past iGEM (International Genetically Engineered Machine) competition results from 2015 to 2025 — including grand prize winners, runners-up, finalists, gold/silver/bronze medal recipients, special prize winners, village (track) award winners, and community awards. Use this skill whenever the user asks about who won what at iGEM in a past year, which teams placed in a specific competition year, what country or university won a particular award, how many medals were awarded, what tracks existed in a given year, or any historical iGEM results question. Also use when comparing winning teams across years, identifying patterns in winning projects, or building lists of past iGEM teams for outreach. Trigger on phrases like "iGEM 2024 winner", "who won iGEM", "past iGEM results", "iGEM gold medals", "iGEM grand prize", "iGEM finalists", "iGEM teams in a given year", "iGEM track award winner", or any retrospective question about iGEM competitions.
---

# iGEM Past Winners

Look up historical iGEM competition results — winners, medalists, and award recipients — from 2015 to 2025.

## When to use

Invoke this skill for any question about past iGEM competition results:
- *"Who won iGEM in 2023?"*
- *"What teams got gold medals in 2024?"*
- *"How many teams competed in 2020?"*
- *"Has any team from <country> ever won the grand prize?"*
- *"What was the winning project in <year>?"* (Note: this skill has *who* won, not the project descriptions — for project content, the user would need to visit the team's wiki, the URL of which is included in the data.)
- *"What special prizes existed in 2017?"*
- *"Compare the 2024 vs 2025 grand prize winners."*

For questions about how to win iGEM, medal criteria, or how the competition is structured today, use the `igem-competition-helper` skill instead. This skill is purely retrospective — *who* won, *where* they were from, *which* award they received.

## Knowledge base

This skill ships with two data files:

**`igem_past_results.jsonl`** — 88 structured documents (~128K characters). One JSONL line per document. Documents are organized as 8 per year × 11 years (2015–2025):

For each year:
1. **Overview** — total teams, regional breakdown, awards available
2. **Grand prize winners and runners-up** (incl. finalists)
3. **Special prize winners** (with award descriptions)
4. **Village (track) awards**
5. **Gold medal recipients** (full list, by section)
6. **Silver medal recipients** (full list, by section)
7. **Bronze medal recipients** (full list, by section)
8. **Community awards**

Each document has:
```json
{
  "id": "igem_results_<year>_<type>",
  "type": "past_results",
  "section": "past_results",
  "name": "<year>_<type>",
  "year": 2024,
  "url": "https://competition.igem.org/results/<year>?tab=<tab>",
  "title": "...",
  "content": "Markdown-formatted result listing"
}
```

**`igem_teams_index.jsonl`** — 3,747 entries, one team per line. Pure metadata for fast lookup of any team that competed 2015–2025:

```json
{
  "year": 2024,
  "name": "Heidelberg",
  "country": "DEU",
  "city": "Heidelberg",
  "region": "europe",
  "section": "overgrad",
  "organiserType": "higher-education",
  "wikiURL": "https://2024.igem.wiki/heidelberg",
  "isRemote": false
}
```

Use this index to answer "did <team> compete in <year>?" or "what was <team>'s wiki URL for <year>?" without loading the larger results docs.

## How to answer questions

### Step 1 — Identify the question type

| Question type | Best file | Search pattern |
|---|---|---|
| "Who won iGEM in <year>?" | `igem_past_results.jsonl` | filter by `name = <year>_grand_prize` |
| "What got gold in <year>?" | `igem_past_results.jsonl` | filter by `name = <year>_medals_gold` |
| "What special prizes existed in <year>?" | `igem_past_results.jsonl` | filter by `name = <year>_special_prizes` |
| "How many teams competed in <year>?" | `igem_past_results.jsonl` | filter by `name = <year>_overview` |
| "Did <team> compete in <year>?" | `igem_teams_index.jsonl` | filter by `year` and `name` |
| "What is <team>'s wiki URL?" | `igem_teams_index.jsonl` | filter by `name` (and `year` if known) |
| "Compare winners across years" | `igem_past_results.jsonl` | load multiple years' grand_prize docs |

### Step 2 — Retrieve

Useful `jq` patterns:

```bash
# Grand prize winners for 2024
jq -c 'select(.name=="2024_grand_prize")' igem_past_results.jsonl

# All gold medal docs for the past 5 years
jq -c 'select(.name | test("_medals_gold$")) | select(.year >= 2020)' igem_past_results.jsonl

# Find a specific team in the index
jq -c 'select(.name=="Heidelberg")' igem_teams_index.jsonl

# Count teams per year
jq -c '.year' igem_teams_index.jsonl | sort | uniq -c

# Find all teams from a country in a specific year
jq -c 'select(.country=="DEU" and .year==2024)' igem_teams_index.jsonl
```

### Step 3 — Format the answer

When answering award questions, lead with the most specific result:
- *"In 2025, the Grand Prize Winner was McGill (Montreal, Canada) in the Undergrad section, and Brno Czech Republic in the Overgrad section."*

Always include the **section** (Undergrad / Overgrad / High School), because iGEM has split prizes by section since 2013. Don't just say "X won iGEM 2024" — clarify which section.

### Step 4 — Cite the source URL

Each document includes a `url` field pointing to the relevant `competition.igem.org/results/<year>?tab=<tab>` page. Always cite this so users can verify.

### Step 5 — Acknowledge gaps

This skill has **structured data only** — it knows *who* won and *where they were from*, but not *what their project was about*. If a user asks "what was the winning project about?", direct them to the team's wiki URL (which is in the data). For example: *"McGill won in 2025 — you can see their full project at https://2025.igem.wiki/mcgill."*

## Coverage and important caveats

- **Years covered:** 2015 through 2025 (11 years).
- **Teams covered:** all 3,747 teams that participated in any of those years.
- **Sections:** Undergrad, Overgrad (since 2013), and High School (where applicable).
- **Award types covered:** grand prize, runners-up, finalists, gold/silver/bronze medals, special prizes, village (track) awards, community awards.
- **Not covered:** project content (wiki text), parts contributions, judge comments, scores. The skill has the *outcome* of judging, not the *substance* of projects.
- **Sources:** all data is from `api.igem.org/v1` (the live iGEM API) — specifically `/competitions/{uuid}/awards/results` and `/teams?year=`. It reflects what the official iGEM site shows on its results pages.
- **Older years (2004–2014):** not included in this scrape. If a user asks about earlier years, acknowledge the gap and direct them to `https://competition.igem.org/results/<year>` for the official record.

## When to defer

If the user asks about *current-year* judging criteria, *how to win* a particular award, or what makes a project medal-worthy in general, switch to the `igem-competition-helper` skill. This skill answers retrospective "who won what" questions; the competition-helper skill answers prescriptive "how to do well" questions, and also covers technical topics like parts registry, DNA assembly, and chassis organisms.

If the user asks about the *technical content* of a winning project (parts used, assembly methods, chassis), point them to the team's wiki URL — this skill only has award metadata, not wiki content.
