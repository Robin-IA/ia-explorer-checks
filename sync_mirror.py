#!/usr/bin/env python3
"""Push `main` to the Internet Archive Canada mirror, if it is safe to.

    python sync_mirror.py            # check, report, and push if clean
    python sync_mirror.py --check    # check and report; push nothing

**The mirror is one-way.** `Robin-IA/ia-explorer-checks` is the source
and `internetarchivecanada/ia-explorer-checks` is a copy for
colleagues to read. Nothing is ever committed to the mirror, and nothing is
ever pulled from it — that is what keeps it from becoming a second history to
merge. Issues are disabled there for the same reason: one tracker.

This exists because the failure mode is silent. Pushing a broken `main`, or
pushing while a branch is checked out, or pushing something that has not
reached `origin` yet, all leave a mirror that looks fine and is not. So every
condition is checked and named before anything is pushed, and a failure says
which one.

## The conditions

1. **On `main`.** The mirror only ever carries `main`; pushing a feature
   branch to it would publish work in progress.
2. **Clean tree.** Uncommitted changes mean the mirror would be a commit
   behind what was tested, and nobody would know which.
3. **`main` matches `origin/main`.** The source of truth is `origin`. If
   local is ahead, push there first; if behind, pull. A mirror ahead of the
   source is the worst of the three states, because the source is where
   anybody looks.
4. **The mirror has no commits of its own.** The moment it has one it is a
   second history, and a push that would discard it should say so rather than
   fail cryptically. The check also reports whether the *content* differs,
   because history-only divergence is safe to force and content divergence is
   not.
5. **Everything compiles and the tests pass.** A mirror is read by people
   who did not watch it being made.

## Cadence

After each merge to `main` that colleagues should see. The mirror being a
few days behind costs nothing, while an automatic push of an untested `main`
costs a colleague's afternoon.
"""

import argparse
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
MIRROR = "iac"
SOURCE = "origin"


def run(*args, check=False):
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise SystemExit(f"  {' '.join(args)} failed:\n{r.stderr.strip()}")
    return r


def git(*args, check=False):
    return run("git", *args, check=check)


def conditions():
    """Every reason not to push, named. Empty list means it is safe."""
    problems = []

    branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if branch != "main":
        problems.append(f"on branch {branch!r}, not main — the mirror only "
                        f"ever carries main")

    dirty = git("status", "--porcelain").stdout.strip()
    if dirty:
        n = len(dirty.splitlines())
        problems.append(f"{n} uncommitted change(s) — commit or stash first, "
                        f"or the mirror lags what was tested")

    remotes = {line.split()[0] for line in
               git("remote").stdout.strip().splitlines() if line.strip()}
    for name in (SOURCE, MIRROR):
        if name not in remotes:
            problems.append(f"no remote named {name!r}")
    if problems:
        return problems

    git("fetch", "--quiet", SOURCE)
    local = git("rev-parse", "main").stdout.strip()
    upstream = git("rev-parse", f"{SOURCE}/main").stdout.strip()
    if local != upstream:
        ahead = git("rev-list", "--count",
                    f"{SOURCE}/main..main").stdout.strip()
        behind = git("rev-list", "--count",
                     f"main..{SOURCE}/main").stdout.strip()
        problems.append(
            f"main and {SOURCE}/main disagree — {ahead} ahead, {behind} "
            f"behind. {SOURCE} is the source of truth; reconcile there first")

    # The mirror having commits of its own is the one failure this script
    # existed for and did not check. It counted `iac/main..main` only, so a
    # mirror that was simultaneously ahead reported as merely behind and then
    # failed on the push - which is how somebody reaches for --force without
    # knowing what it would discard.
    #
    # Measured 2026-09-04: the README was edited on the mirror through
    # GitHub's own edit button as well as on the source, so the mirror had
    # two commits and the same final text. History diverged, content did not,
    # and the distinction is the whole point of reporting it.
    git("fetch", "--quiet", MIRROR)
    extra = git("rev-list", "--count", f"main..{MIRROR}/main").stdout.strip()
    if extra and extra != "0":
        identical = git("diff", "--quiet", "main",
                        f"{MIRROR}/main").returncode == 0
        verdict = ("the content is identical, so this is history-only "
                   "divergence and forcing discards nothing"
                   if identical else
                   "THE CONTENT DIFFERS TOO - read it before forcing, "
                   "because forcing discards it")
        problems.append("\n".join([
            f"{MIRROR}/main has {extra} commit(s) that main does not. "
            f"Something was committed to the mirror directly, which is what "
            f"makes it a second history.",
            f"      Checked: {verdict}.",
            f"      Look:    git log main..{MIRROR}/main",
            f"               git diff main {MIRROR}/main",
            f"      Fix:     git push {MIRROR} main --force",
        ]))

    compile_check = run(sys.executable, "-m", "compileall", "-q",
                        str(ROOT / "skills"))
    if compile_check.returncode != 0:
        problems.append("skills/ does not compile — "
                        + compile_check.stdout.strip()[:120])

    tests = run(sys.executable, "-m", "pytest", "-q", str(ROOT / "tests"))
    if tests.returncode != 0:
        problems.append("tests fail — " + tests.stdout.strip()[-160:])

    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report only; push nothing")
    args = ap.parse_args()

    print(f"  source: {SOURCE}   mirror: {MIRROR}\n")
    problems = conditions()
    if problems:
        print(f"  NOT pushing. {len(problems)} condition(s) unmet:\n")
        for p in problems:
            print(f"    - {p}")
        return 1

    git("fetch", "--quiet", MIRROR)
    local = git("rev-parse", "main").stdout.strip()
    mirror = git("rev-parse", f"{MIRROR}/main").stdout.strip()
    if local == mirror:
        print("  mirror already matches main. Nothing to do.")
        return 0

    behind = git("rev-list", "--count",
                 f"{MIRROR}/main..main").stdout.strip()
    print(f"  all conditions met; mirror is {behind} commit(s) behind")
    if args.check:
        print("  --check given, so nothing pushed")
        return 0

    push = git("push", MIRROR, "main")
    if push.returncode != 0:
        print(f"  push failed:\n{push.stderr.strip()}")
        return 1
    print(f"  pushed {local[:8]} to {MIRROR}/main")
    return 0


if __name__ == "__main__":
    sys.exit(main())
