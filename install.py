#!/usr/bin/env python3
"""Install the skill into Claude Code, so it works from any directory.

    python3 install.py           # copy skills/explorer-checks to ~/.claude/skills/
    python3 install.py --check   # say whether the installed copy is current

This is a copy, not a link, so it does not depend on the checkout staying
put. After pulling a change, run it again. --check tells you whether you
need to.
"""

import argparse
import filecmp
import pathlib
import shutil
import sys

SRC = pathlib.Path(__file__).resolve().parent / "skills" / "explorer-checks"
DEST = pathlib.Path.home() / ".claude" / "skills" / "explorer-checks"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")


def differs(a, b):
    cmp = filecmp.dircmp(a, b, ignore=["__pycache__"])
    if cmp.left_only or cmp.right_only or cmp.diff_files:
        return True
    return any(differs(a / d, b / d) for d in cmp.common_dirs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    stale = not DEST.exists() or differs(SRC, DEST)
    if args.check:
        print(f"{DEST}: {'out of date' if stale else 'current'}")
        return 1 if stale else 0
    if DEST.exists():
        shutil.rmtree(DEST)
    shutil.copytree(SRC, DEST, ignore=IGNORE)
    print(f"installed {SRC.name} to {DEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
