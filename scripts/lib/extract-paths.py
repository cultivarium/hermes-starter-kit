#!/usr/bin/env python3
"""Print `path:` values from the named top-level YAML section of a manifest.

Stops at the next top-level key (column-0). Avoids a YAML library dependency.

Special case: if <section> is "starter_recipes_to_advertise", emits the
list items themselves (each line "- name") rather than path values.

Usage:
    extract-paths.py <manifest.yaml> <section>
"""
import re
import sys


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: extract-paths.py <manifest> <section>\n")
        return 2

    manifest, section = argv[0], argv[1]
    in_section = False
    section_re = re.compile(rf"^{re.escape(section)}:\s*$")
    list_section = section == "starter_recipes_to_advertise"

    with open(manifest) as f:
        for line in f:
            if section_re.match(line):
                in_section = True
                continue
            if in_section:
                if re.match(r"^\S", line):  # next top-level key, stop
                    break
                if list_section:
                    m = re.match(r"\s*-\s+(\S+)\s*$", line)
                    if m:
                        print(m.group(1))
                else:
                    m = re.search(r"\bpath:\s+(\S+)", line)
                    if m:
                        print(m.group(1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
