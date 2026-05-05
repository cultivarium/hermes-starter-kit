#!/usr/bin/env python3
"""Refresh release-derived fields in manifest.yaml.

Two fields are refreshed:

  1. `released:` — set to today's date in ISO format (UTC).
  2. Per-skill / per-recipe `sha256:` — replaced with a content-rollup
     hash so the manifest can be used for external integrity checks.

The installer (scripts/lib/install-files.py) does NOT consume the
`sha256:` field — it computes per-file sha256s on disk and tracks them
in .starter-kit-state.json. The field exists for release-time integrity
and external auditing, hence the placeholder dance.

Rollup definition (deterministic):

  * Skill (path is a directory): sha256 over the concatenation of
    `<rel-path-from-skill-root>\\t<sha256>\\n` lines, sorted by rel-path.
  * Recipe (path is a single file): sha256 of the file's bytes.

Usage:
    update-release-fields.py manifest.yaml [--check]

`--check` exits non-zero if any field would change (CI-friendly).
The default mode rewrites the file in place using line-level edits
(no PyYAML round-trip — preserves comments, ordering, formatting).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import re
import sys
from pathlib import Path


def _file_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def rollup(repo_root: Path, rel_path: str) -> str:
    """Deterministic content-rollup hash for a skill dir or recipe file."""
    target = repo_root / rel_path
    if target.is_dir():
        lines: list[str] = []
        for f in sorted(target.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(target).as_posix()
            lines.append(f"{rel}\t{_file_sha256(f)}\n")
        return hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()
    if target.is_file():
        return _file_sha256(target)
    raise FileNotFoundError(f"manifest entry references missing path: {rel_path}")


_PATH_RE = re.compile(r"^\s*path:\s*(\S+)\s*$")
_SHA_RE  = re.compile(r"^(\s*sha256:\s*)(\S+)(\s*)$")
_RELEASED_RE = re.compile(r'^(\s*released:\s*)("[^"]*"|\S+)(\s*.*)$')


def refresh(manifest_path: Path, *, check: bool) -> int:
    repo_root = manifest_path.parent
    today = _dt.datetime.now(_dt.timezone.utc).date().isoformat()

    original = manifest_path.read_text().splitlines(keepends=True)
    out: list[str] = []
    pending_path: str | None = None
    changed = False

    for line in original:
        # Track the most recent `path:` so we can compute the rollup
        # when the matching `sha256:` line appears next.
        m_path = _PATH_RE.match(line)
        if m_path:
            pending_path = m_path.group(1)
            out.append(line)
            continue

        m_sha = _SHA_RE.match(line)
        if m_sha and pending_path is not None:
            new_sha = rollup(repo_root, pending_path)
            new_line = f"{m_sha.group(1)}{new_sha}{m_sha.group(3)}"
            if not new_line.endswith("\n") and line.endswith("\n"):
                new_line += "\n"
            if new_line != line:
                changed = True
            out.append(new_line)
            pending_path = None
            continue

        m_rel = _RELEASED_RE.match(line)
        if m_rel:
            new_line = f'{m_rel.group(1)}"{today}"{m_rel.group(3)}'
            if not new_line.endswith("\n") and line.endswith("\n"):
                new_line += "\n"
            if new_line != line:
                changed = True
            out.append(new_line)
            continue

        out.append(line)

    if check:
        return 1 if changed else 0

    if changed:
        manifest_path.write_text("".join(out))
        print(f"updated: {manifest_path}")
    else:
        print(f"already up-to-date: {manifest_path}")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("manifest", type=Path, help="path to manifest.yaml")
    ap.add_argument("--check", action="store_true",
                    help="exit non-zero if any field would change; do not write")
    args = ap.parse_args(argv)
    if not args.manifest.is_file():
        print(f"not a file: {args.manifest}", file=sys.stderr)
        return 2
    return refresh(args.manifest, check=args.check)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
