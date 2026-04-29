#!/usr/bin/env python3
"""Install skills/recipes from the starter kit into the user's Goose config.

Per-file behaviour, driven by .starter-kit-state.json:

  * If the destination file does not exist:                    install fresh.
  * If destination matches what we last wrote (sha256 in state): overwrite
    unless its content already equals the new source (no-op).
  * If destination differs from what we last wrote (user edit): preserve;
    leave the on-disk file alone and do NOT update state for that file.

Usage:
    install-files.py <starter_dir> <config_dir> <state_file> \\
                     <skill_paths_space_separated> <recipe_paths_space_separated>

Both *_paths arguments are whitespace-separated relative paths from
<starter_dir> (e.g. "skills/ncbi-datasets" or "recipes/onboarding.yaml").
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def main(argv):
    if len(argv) != 5:
        sys.stderr.write(
            "usage: install-files.py <starter_dir> <config_dir> <state_file> "
            "<skill_paths> <recipe_paths>\n"
        )
        return 2

    starter_dir = Path(argv[0])
    config_dir  = Path(argv[1])
    state_path  = Path(argv[2])
    skill_paths  = argv[3].split()
    recipe_paths = argv[4].split()

    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    new_state = dict(state)

    stats = {
        "installed": 0,
        "updated": 0,
        "preserved_user_edit": 0,
        "missing_source": 0,
    }

    def install_file(src: Path, dst: Path, key: str) -> None:
        src_sha = sha256(src)
        if dst.exists():
            on_disk_sha = sha256(dst)
            recorded = state.get(key)
            if on_disk_sha == src_sha:
                new_state[key] = src_sha
                return
            if recorded and on_disk_sha != recorded:
                stats["preserved_user_edit"] += 1
                print(f"  ~ preserved (user-modified): {key}")
                return
            stats["updated"] += 1
        else:
            stats["installed"] += 1
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        new_state[key] = src_sha

    def install_dir(src: Path, dst_root: Path, key_prefix: str) -> None:
        if not src.is_dir():
            stats["missing_source"] += 1
            print(f"  ! missing source dir: {src}", file=sys.stderr)
            return
        for f in src.rglob("*"):
            if f.is_dir():
                continue
            rel = f.relative_to(src)
            install_file(f, dst_root / rel, f"{key_prefix}/{rel}")

    for sp in skill_paths:
        name = Path(sp).name
        install_dir(starter_dir / sp, config_dir / "skills" / name, f"skills/{name}")

    for rp in recipe_paths:
        name = Path(rp).name
        src = starter_dir / rp
        if src.is_file():
            install_file(src, config_dir / "recipes" / name, f"recipes/{name}")
        else:
            stats["missing_source"] += 1
            print(f"  ! missing recipe: {src}", file=sys.stderr)

    state_path.write_text(json.dumps(new_state, indent=2, sort_keys=True))
    print(json.dumps({"stats": stats, "tracked_files": len(new_state)}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
