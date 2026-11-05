#!/usr/bin/env python3
"""Install the skill into Claude Code, so it works from any directory.

    python3 install.py           # copy skills/explorer-checks to ~/.claude/skills/
    python3 install.py --check   # say whether the installed copy is current

This is a copy, not a link, so it does not depend on the checkout staying
put. After pulling a change, run it again. --check tells you whether you
need to.

Run it with the Python the checks should use, normally the checker's own
virtual environment (.venv/bin/python install.py; see SETUP.md). The path
of that Python is written to PYTHON in the installed skill, and the skill
runs its scripts with it, so the packages they import are always there.
"""

import argparse
import filecmp
import pathlib
import shutil
import sys

SRC = pathlib.Path(__file__).resolve().parent / "skills" / "explorer-checks"
DEST = pathlib.Path.home() / ".claude" / "skills" / "explorer-checks"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")
RECORD = "PYTHON"   # written at install, so not in the source tree


def differs(a, b):
    cmp = filecmp.dircmp(a, b, ignore=["__pycache__", RECORD])
    if cmp.left_only or cmp.right_only or cmp.diff_files:
        return True
    return any(differs(a / d, b / d) for d in cmp.common_dirs)


def main():
    if sys.version_info < (3, 10):  # noqa: UP036 - the point is to catch an old python3
        sys.exit(f"Python {sys.version.split()[0]} is too old: the checks "
                 "need 3.10 or newer (3.12 or newer recommended). Run "
                 "python3 check_setup.py to see what to install.")
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
    (DEST / RECORD).write_text(sys.executable + "\n", encoding="utf-8")
    print(f"installed {SRC.name} to {DEST}")
    print(f"the skill will run its checks with {sys.executable}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
