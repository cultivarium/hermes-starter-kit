"""Query the iGEM projects table.

Usage:
    python -m scripts.query --keyword "phage therapy" --year-min 2020 --medal Gold

All filters are AND-combined. Keyword search is case-insensitive substring match
across Project_Title and Project_Description.

Outputs a TSV-formatted table to stdout. Use --json for JSON output.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "igem_projects.csv"

# Sections "Collegiate", "Undergrad", "Overgrad" all describe college-level
# teams across different iGEM eras. Treat as a group when the user asks for
# "undergrad" / "college".
# Lower-cased to handle data-source casing inconsistencies (e.g. 2025 uses
# lowercase "undergrad" instead of "Undergrad" — comparison is case-insensitive).
COLLEGE_SECTIONS = {"undergrad", "overgrad", "collegiate"}

# Village taxonomy has been heavily renamed/split over the years. A naive
# `--village Environment` for recent years drops to zero in 2024+ even though
# environmental work is still happening under successor labels. The families
# below group historical and current village names so users can ask for the
# "environment family" or the "manufacturing family" without manually unioning.
# Stored lower-cased for case-insensitive matching against the Village column.
# See SKILL.md caveat #7 for the full rename history.
VILLAGE_FAMILIES = {
    "environment": {
        "environment", "bioremediation", "climate crisis", "conservation", "agriculture",
    },
    "manufacturing": {
        "manufacturing", "biomanufacturing",
    },
    "health": {
        "health & medicine", "health/medicine", "therapeutics", "diagnostics",
        "oncology", "infectious diseases",
    },
    "software": {
        "software", "software tools", "software & ai", "information processing",
    },
    "food": {
        "food & nutrition", "food & energy", "food/energy",
    },
}


def load_rows() -> list[dict]:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        # Drop trailing empty-string columns from the source CSV.
        return [
            {k: (v or "").strip() for k, v in row.items() if k}
            for row in reader
        ]


def keyword_match(row: dict, all_keywords: list[str], any_keywords: list[str]) -> bool:
    haystack = " ".join([
        row.get("Project_Title", ""),
        row.get("Project_Description", ""),
    ]).lower()
    if all_keywords and not all(kw.lower() in haystack for kw in all_keywords):
        return False
    if any_keywords and not any(kw.lower() in haystack for kw in any_keywords):
        return False
    return True


def filter_rows(rows: list[dict], args: argparse.Namespace) -> list[dict]:
    out = []
    all_kw = args.keyword or []
    any_kw = args.any_keyword or []
    for r in rows:
        if not keyword_match(r, all_kw, any_kw):
            continue
        if args.year_min and int(r["Year"]) < args.year_min:
            continue
        if args.year_max and int(r["Year"]) > args.year_max:
            continue
        if args.year and int(r["Year"]) != args.year:
            continue
        if args.team and args.team.lower() not in r["Team"].lower():
            continue
        if args.medal and r.get("Medal", "").lower() != args.medal.lower():
            continue
        if args.village and args.village.lower() not in r.get("Village", "").lower():
            continue
        if args.village_family:
            family = VILLAGE_FAMILIES.get(args.village_family.lower())
            if family is None or r.get("Village", "").lower() not in family:
                continue
        if args.section:
            sec = r.get("Section", "")
            if args.section.lower() == "college":
                if sec.lower() not in COLLEGE_SECTIONS:
                    continue
            elif sec.lower() != args.section.lower():
                continue
        if args.region and args.region.lower() not in r.get("Region", "").lower():
            continue
        if args.country and args.country.lower() not in r.get("Country", "").lower():
            continue
        if args.species and args.species.lower() not in r.get("Species", "").lower():
            continue
        if args.prize and args.prize.lower() not in r.get("Prizes", "").lower():
            continue
        out.append(r)
    return out


def render_table(rows: list[dict], max_rows: int, columns: list[str]) -> str:
    if not rows:
        return "(no matches)"
    truncated = rows[:max_rows]
    header = "\t".join(columns)
    lines = [header]
    any_desc_truncated = False
    for r in truncated:
        vals = []
        for c in columns:
            v = r.get(c, "")
            # Trim long descriptions for table display.
            if c == "Project_Description" and len(v) > 200:
                v = v[:197] + "..."
                any_desc_truncated = True
            v = re.sub(r"\s+", " ", v)
            vals.append(v)
        lines.append("\t".join(vals))
    if len(rows) > max_rows:
        lines.append(f"... ({len(rows) - max_rows} more rows; use --max-rows to see more)")
    lines.append(f"\nTotal matches: {len(rows)}")
    if any_desc_truncated:
        lines.append("Note: Project_Description values were truncated to 200 chars for display. "
                     "Use --json for full descriptions.")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--keyword", action="append",
                   help="Substring match across title + description. Repeat for AND.")
    p.add_argument("--any-keyword", action="append",
                   help="Substring match across title + description; ANY of these matches. "
                        "Repeat for OR. Use for synonym broadening (e.g. --any-keyword 'phage therapy' "
                        "--any-keyword 'phage-based' --any-keyword 'bacteriophage'). Combines with --keyword "
                        "as: (all --keyword AND) AND (any --any-keyword OR).")
    p.add_argument("--year", type=int)
    p.add_argument("--year-min", type=int)
    p.add_argument("--year-max", type=int)
    p.add_argument("--team")
    p.add_argument("--medal", help="Gold / Silver / Bronze")
    p.add_argument("--village", help="e.g. Therapeutics, Environment, Diagnostics")
    p.add_argument("--village-family",
                   help="Group of related villages spanning iGEM's renames. Values: "
                        "environment (Environment+Bioremediation+Climate Crisis+Conservation+Agriculture), "
                        "manufacturing (Manufacturing+Biomanufacturing), "
                        "health (Health & Medicine+Therapeutics+Diagnostics+Oncology+Infectious Diseases), "
                        "software (Software+Software Tools+Software & AI+Information Processing), "
                        "food (Food & Nutrition+Food & Energy+Food/Energy). "
                        "Use this for cross-year thematic queries instead of --village.")
    p.add_argument("--section",
                   help="High School / Undergrad / Overgrad / Collegiate / 'college' (collapses the three college variants)")
    p.add_argument("--region")
    p.add_argument("--country")
    p.add_argument("--species")
    p.add_argument("--prize", help="Substring match in Prizes column, e.g. 'Best Wiki', 'Grand Prize'")
    p.add_argument("--max-rows", type=int, default=25)
    p.add_argument("--columns", default="Year,Team,Project_Title,Village,Section,Country,Medal,Wiki_Link",
                   help="Comma-separated columns to display.")
    p.add_argument("--json", action="store_true",
                   help="Emit JSON instead of TSV.")
    p.add_argument("--count-only", action="store_true",
                   help="Print only the match count.")
    args = p.parse_args()

    rows = load_rows()

    # Validate filter values against the data so a typo doesn't silently return 0.
    # Warns on stderr only — the CLI still runs the (possibly empty) query.
    def _column_values(col):
        return {r.get(col, "").lower() for r in rows if r.get(col)}

    def _warn_unknown(flag, value, col, mode="exact"):
        if not value:
            return
        vals = _column_values(col)
        v = value.lower()
        if mode == "substring":
            ok = any(v in x for x in vals)
        else:
            ok = v in vals
        if not ok:
            sys.stderr.write(
                f"warning: --{flag} {value!r} matches no rows in column {col!r}. "
                f"Check spelling or run without this filter.\n"
            )

    _warn_unknown("medal", args.medal, "Medal", mode="exact")
    if args.section and args.section.lower() != "college":
        _warn_unknown("section", args.section, "Section", mode="exact")
    _warn_unknown("village", args.village, "Village", mode="substring")
    if args.village_family and args.village_family.lower() not in VILLAGE_FAMILIES:
        sys.stderr.write(
            f"warning: --village-family {args.village_family!r} is not a known family. "
            f"Valid values: {', '.join(sorted(VILLAGE_FAMILIES))}.\n"
        )
    _warn_unknown("region", args.region, "Region", mode="substring")
    _warn_unknown("country", args.country, "Country", mode="substring")
    if args.year and not (2004 <= args.year <= 2025):
        sys.stderr.write(
            f"warning: --year {args.year} is outside the data range 2004–2025.\n"
        )

    matches = filter_rows(rows, args)

    # Stable display order: most recent year first, alphabetical team within year.
    matches.sort(key=lambda r: (-int(r["Year"]), r["Team"]))

    if args.count_only:
        print(len(matches))
        return 0

    if args.json:
        print(json.dumps(matches[: args.max_rows], indent=2))
        if len(matches) > args.max_rows:
            print(f"// truncated; total matches: {len(matches)}", file=sys.stderr)
        return 0

    columns = [c.strip() for c in args.columns.split(",") if c.strip()]
    print(render_table(matches, args.max_rows, columns))
    return 0


if __name__ == "__main__":
    sys.exit(main())
