---
name: igem-competition-helper
description: >
  Help iGEM (International Genetically Engineered Machine) competition participants prepare for the competition and put together their projects. Use this skill whenever a user asks about iGEM, including: starting a team, registration, fundraising, deliverables (wiki, judging form, presentation video, attributions, part pages, judging session), medal criteria (bronze/silver/gold), special prizes, judging, the iGEM cycle and Jamboree, villages, human practices, responsible design, biosafety and the white list of approved organisms, human subjects research, the parts registry, distribution kits, DNA assembly (Golden Gate/Type IIS), chassis (bacteria, mammalian, yeast, plant), high school iGEM teams and CTOEs, and post-iGEM startups. Trigger on "iGEM", "Jamboree", "synthetic biology competition", or any specific iGEM-related question.
---

# iGEM Competition Helper

Help iGEM participants prepare for the competition and put together their projects, grounded in the official iGEM website content.

## When to use

Invoke this skill any time the user asks something related to iGEM — registration, deliverables, judging, medals, special prizes, safety, human practices, parts registry, chassis, the Jamboree, starting a team, fundraising, high school teams, post-iGEM startups, or anything else about the competition.

## Knowledge base

This skill comes with a curated knowledge base scraped from the official iGEM websites:

- `igem_training_data.jsonl` — 87 documents (~745K characters) covering every major iGEM topic relevant to participants. Sources include `igem.org`, `competition.igem.org`, `technology.igem.org`, `responsibility.igem.org`, `community.igem.org`, `startups.igem.org`, `jamboree.igem.org`, `registry.igem.org`, `blog.igem.org`, plus structured data from `api.igem.org/v1`.

Each line of the JSONL is a JSON object with this schema:

```json
{
  "id": "igem_<section>_<name>",
  "type": "webpage" | "blog_post" | "structured_data",
  "section": "competition" | "technology" | "responsibility" | "community" | "main" | "startups" | "villages" | "blog" | "registry",
  "name": "short_identifier",
  "url": "https://...",
  "title": "Page title",
  "content": "Clean text content of the page",
  "char_count": 12345
}
```

### Section coverage

| Section | Docs | What it covers |
|---|---|---|
| `competition` | 22 | Registration, deliverables (wiki, judging form, attributions, part pages, presentation video, judging session), medal criteria, special prizes, judging, calendar, FAQ, sponsorships, fundraising, starting a team, navigating iGEM, high school teams |
| `technology` | 12 | Engineering principles, DNA assembly (Golden Gate / Type IIS), distribution handbook, parts distribution, chassis (mammalian, yeast), tech committee |
| `responsibility` | 14 | Human practices (what it is, how to do it well), integrated HP, surveys & interviews guidance, white list of approved organisms, biosafety policies, human subjects research, human experimentation rules, responsible design, conference reports |
| `blog` | 27 | Practical how-to articles: starting a team, anatomy of a team, fundraising, the iGEM cycle, diverse and inclusive teams, working with animals, biosafety overviews, high school challenges, CTOEs, AI in synbio, cell-free systems, infectious diseases, synbio in space, fashion/cosmetics, startup showcases, policy engagement |
| `community` | 4 | Community overview, history, synbio topics, projects |
| `startups` | 3 | Startups overview, Venture Foundry, incubators and VCs |
| `main` | 2 | iGEM homepage, vision and about |
| `villages` | 2 | Villages overview, 2026 villages structured data |
| `registry` | 1 | 2025 registry announcement |

## How to answer iGEM questions

### Step 1 — Retrieve relevant documents

When the user asks an iGEM question, search `igem_training_data.jsonl` for documents whose `content`, `title`, or `name` field matches the question. Use `jq` from the shell:

```bash
# Find docs in a specific section
jq -c 'select(.section=="competition")' igem_training_data.jsonl

# Search by keyword across all docs
jq -c 'select(.content | test("medal"; "i"))' igem_training_data.jsonl

# Get a specific doc by name
jq -c 'select(.name=="judging_medals")' igem_training_data.jsonl
```

For richer matching, pick the 3–5 documents whose `name`, `title`, or content snippet most closely matches the question's intent. Read their full `content` fields before answering.

### Step 2 — Section-first triage

Use `section` as a fast filter before searching content. Mapping common questions to sections:

- *"what do I need to do for gold medal?"* → `competition` (esp. `judging_medals`)
- *"how do I run a survey for human practices?"* → `responsibility` (esp. `guidance_surveys`, `hp_what_is`)
- *"can I use this organism?"* → `responsibility` (esp. `safety_whitelist`, `guidance_whitelist`, `safety_organisms`)
- *"how does Golden Gate assembly work in iGEM?"* → `technology` (esp. `dna_assembly`, `golden_gate_assembly`)
- *"how do I start a team?"* → `blog` + `competition` (esp. `how_to_start_team`, `starting_a_team`, `anatomy_of_team`)
- *"what's the deadline for X?"* → `competition` (esp. `phases_timeline_2026`, `deliverables_2026`, `calendar`)
- *"is iGEM worth it for a startup?"* → `startups` + `blog` (esp. `venture_foundry`, `fredsense_startup`, `startup_showcase_2025`)

### Step 3 — Answer with citation

Always cite the `url` of the source document(s) used. iGEM rules and deadlines change year to year, so participants benefit from being able to verify on the official site. A natural pattern:

> *"For gold medal you need to [...] You can read the full criteria at https://competition.igem.org/judging/medals."*

### Step 4 — Flag freshness when relevant

The knowledge base was scraped on a specific date. For time-sensitive answers (deadlines, current year's tracks, current sponsors), remind the user to verify on the official site. The structured 2026 data (`phases_timeline_2026`, `deliverables_2026`, `awards_2026`, `villages_2026`) is the freshest content; older blog posts may reference outdated rules.

## Tips for high-quality answers

- **Distinguish iGEM-specific advice from general synbio advice.** Many participants come to iGEM having read general synbio papers — the rules of the competition are often what they actually need to know, not the science.
- **Human Practices is more than outreach.** A common mistake is treating HP as a separate "communications" activity. The knowledge base (esp. `hp_what_is` and the judging criteria) explains that HP should be integrated into the project — informing design choices, not just advertising the project.
- **Medal criteria vs. special prizes are different.** Medals are scored against fixed criteria. Special prizes (best wiki, best part collection, best therapeutics project, etc.) are competitive and require explicit nomination via the judging form. Don't conflate them.
- **High school teams have different rules.** If the user mentions they're in high school, prioritize `hs_challenges`, `hs_experimental`, `ctoe_hs` and the `high_school` competition page. Lab access, instructor roles, and consent rules differ.
- **Be precise about deliverables.** Each deliverable (wiki, judging form, attributions, part pages, presentation video, judging session) has its own rules and deadline. When the user asks "what do I need to submit?", walk them through each one.

## What this skill does NOT cover

- Past competition results and winning projects (excluded by design — could be added later as a separate skill).
- Live or future event registration (always direct the user to the official site).
- Personal account, password, or registration troubleshooting (route to iGEM HQ at hq@igem.org).
