"""Print corpus statistics for the iGEM projects table.

Run this after refreshing data/igem_projects.csv. The output gives the numbers
referenced in SKILL.md (total rows, distinct teams, fill rates, year totals,
section labels, village counts) plus a paste-ready caveat block.

Usage:
    cd <skill-path> && python -m scripts.data_stats

Outputs to stdout. No arguments. Reads from data/igem_projects.csv via
the load_rows() helper in query.py so any schema fix there carries through.
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

# Allow running as `python -m scripts.data_stats` or directly.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from query import load_rows  # noqa: E402


# Columns whose blanks are real "missing" data we care about reporting.
# Wiki_Link and Year are listed for completeness; Prizes/Nominations are
# expected to be sparse (only filled when the project actually won/was
# nominated) so their fill rate is not "missingness" but data semantics.
TRACKED_COLUMNS = [
    "Year",
    "Team",
    "Wiki_Link",
    "Project_Title",
    "Project_Description",
    "Species",
    "Village",
    "Section",
    "Region",
    "Country",
    "Medal",
    "Prizes",
    "Nominations",
]


def _hr(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def main() -> int:
    rows = load_rows()
    n = len(rows)

    print(f"iGEM projects corpus statistics — {n} rows")
    print("=" * 60)

    _hr("Headline numbers (paste into SKILL.md intro)")
    teams = sorted({r["Team"] for r in rows})
    years = sorted({int(r["Year"]) for r in rows})
    print(f"Total rows:                {n}")
    print(f"Distinct team names:       {len(teams)}")
    print(f"Year range:                {years[0]}–{years[-1]} ({len(years)} years)")

    _hr("Fill rate by column")
    print(f"{'column':<22}{'filled':>8}{'pct':>8}")
    for col in TRACKED_COLUMNS:
        filled = sum(1 for r in rows if r.get(col))
        pct = 100 * filled / n
        print(f"{col:<22}{filled:>8}{pct:>7.1f}%")

    _hr("Rows per year")
    by_year = Counter(int(r["Year"]) for r in rows)
    for y in sorted(by_year):
        print(f"  {y}: {by_year[y]}")

    _hr("Section values (verbatim, including casing variants)")
    for v, c in Counter(r.get("Section", "") for r in rows).most_common():
        marker = "  <- watch for casing drift" if v and v != v.title() else ""
        print(f"  {c:>5}  '{v}'{marker}")

    _hr("Medal values")
    for v, c in Counter(r.get("Medal", "") for r in rows).most_common():
        print(f"  {c:>5}  '{v}'")

    _hr("Village values with year span (catches renames/retirements)")
    village_years: dict[str, list[int]] = defaultdict(list)
    for r in rows:
        v = r.get("Village", "")
        if v:
            village_years[v].append(int(r["Year"]))
    print(f"  {'first':>6}{'last':>6}{'count':>7}  village")
    for v in sorted(village_years):
        ys = village_years[v]
        print(f"  {min(ys):>6}{max(ys):>6}{len(ys):>7}  {v}")

    _hr("Region distribution")
    for v, c in Counter(r.get("Region", "") for r in rows).most_common():
        print(f"  {c:>5}  '{v}'")

    _hr("Top 15 countries")
    for v, c in Counter(r.get("Country", "") for r in rows).most_common(15):
        print(f"  {c:>5}  '{v}'")

    _hr("HTML markup in titles (caveat #8 sanity check)")
    entities = sum(1 for r in rows if "&#" in r.get("Project_Title", ""))
    italics = sum(1 for r in rows if "<i>" in r.get("Project_Title", ""))
    print(f"  Titles with HTML entities (&#...;): {entities}")
    print(f"  Titles with <i>...</i> markup:      {italics}")

    # -------- Paste-ready caveat block --------
    _hr("Paste-ready: SKILL.md intro line")
    # Round to nearest 100 to match the existing prose style ("~4,900 projects").
    rounded_rows = round(n, -2)
    rounded_teams = round(len(teams), -2)
    print(
        f"covering 2004–{years[-1]} (~{rounded_rows:,} projects, "
        f"~{rounded_teams:,} teams)"
    )
    print(f"  exact: {n} projects, {len(teams)} distinct team names")

    _hr("Paste-ready: caveat fill-rate numbers")
    species_pct = 100 * sum(1 for r in rows if r.get("Species")) / n
    medal_pct = 100 * sum(1 for r in rows if r.get("Medal")) / n
    wiki_pct = 100 * sum(1 for r in rows if r.get("Wiki_Link")) / n
    prizes_pct = 100 * sum(1 for r in rows if r.get("Prizes")) / n
    noms_pct = 100 * sum(1 for r in rows if r.get("Nominations")) / n
    print(f"  Species fill:        ~{species_pct:.0f}%   (caveat #1)")
    print(f"  Medal fill:          ~{medal_pct:.0f}%   (caveat #4)")
    print(f"  Wiki_Link fill:      ~{wiki_pct:.0f}%  (caveat #6)")
    print(f"  Prizes fill:         ~{prizes_pct:.0f}%   (caveat #5)")
    print(f"  Nominations fill:    ~{noms_pct:.0f}%   (caveat #5)")

    _hr("Paste-ready: latest-year row count (caveat #9)")
    latest = max(years)
    latest_count = by_year[latest]
    second = sorted(years)[-2]
    second_count = by_year[second]
    third = sorted(years)[-3]
    third_count = by_year[third]
    print(
        f"  {latest} row count is ~{latest_count} — comparable to "
        f"{second} ({second_count}) and {third} ({third_count})."
    )

    _hr("Caveat sanity checks")
    # Section casing drift
    sec_values = {r.get("Section", "") for r in rows}
    casing_drift = [(a, b) for a in sec_values for b in sec_values
                    if a and b and a != b and a.lower() == b.lower()]
    if casing_drift:
        print(f"  Section has casing drift — {casing_drift[0]}")
        print(f"  → keep caveat #3 about lowercase 'undergrad'.")
    else:
        print(f"  Section casing is consistent — caveat #3 is no longer needed.")
    # College sections present?
    secs = Counter(r.get("Section", "").lower() for r in rows)
    college_total = secs["undergrad"] + secs["overgrad"] + secs["collegiate"]
    print(f"  College-level rows (undergrad+overgrad+collegiate): {college_total}")
    # Village retirement check — flag retired villages
    cutoff = latest - 1
    retired = [v for v, ys in village_years.items() if max(ys) < cutoff]
    if retired:
        print(f"  Villages not seen since {cutoff}: {len(retired)}")
        for v in sorted(retired):
            ys = village_years[v]
            print(f"    {v} (last: {max(ys)}, total: {len(ys)})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
