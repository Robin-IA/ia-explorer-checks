#!/usr/bin/env python3
"""Say whether this Mac has everything the checks need, and how to fix
whatever is missing. SETUP.md walks through it.

    .venv/bin/python check_setup.py

Run it with the Python the checks will use, normally the checker's own
virtual environment: the packages it looks for have to be installed into
that Python. Each line is OK, MISSING or OPTIONAL, and every line that is
not OK says what to do. Exit status is 0 when everything required is
present.

Written to run on old Pythons too, so it can report that one is too old.
"""

import importlib.util
import pathlib
import shutil
import ssl
import subprocess
import sys
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
MIN_PYTHON = (3, 10)        # playwright, bandit, pip-audit and pytest need it
GOOD_PYTHON = (3, 12)       # 3.10 is past end of life; 3.11 ends 2027-10
MAC = sys.platform == "darwin"
APPLE_STUB = ("/usr/bin/python3", "/Library/Developer/CommandLineTools/",
              "/Applications/Xcode.app/")
VENV_FIX = ("python3 -m venv .venv, then .venv/bin/python -m pip install "
            "-r requirements.txt (SETUP.md, step 3)")
CERT_FIX = ("Homebrew Python: brew reinstall ca-certificates python. "
            "python.org Python: open Applications > Python 3.x and "
            "double-click 'Install Certificates.command'")

# (module to import, what it is for)
PACKAGES = [
    ("html5lib", "HTML parsing (validity)"),
    ("playwright", "drives the browser for the accessibility check"),
    ("ruff", "Python errors (validity)"),
    ("bandit", "Python security"),
    ("pip_audit", "known vulnerabilities in Python dependencies"),
    ("pytest", "runs an explorer's own tests"),
]

rows = []


def row(status, what, detail="", fix=""):
    rows.append((status, what, detail, fix))


def run(cmd):
    try:
        r = subprocess.run(cmd, check=False, capture_output=True,
                           text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, str(e)
    return r.returncode, (r.stdout + r.stderr).strip()


def in_venv():
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def check_python():
    v = sys.version_info
    exe = sys.executable
    found = f"{v.major}.{v.minor}.{v.micro} at {exe}"
    if MAC and not in_venv() and exe.startswith(APPLE_STUB):
        row("MISSING", "a real Python", f"found Apple's own copy, {found}",
            "brew install python, then open a new Terminal "
            "(SETUP.md, step 1)")
        return False
    if v[:2] < MIN_PYTHON:
        row("MISSING", "Python 3.10 or newer", f"found {found}",
            "brew upgrade python, then rebuild the environment: "
            "rm -rf .venv and repeat SETUP.md, step 3")
        return False
    if v[:2] < GOOD_PYTHON:
        row("OK", "Python", f"{found}; 3.12 or newer is recommended")
    else:
        row("OK", "Python", found)
    if in_venv():
        row("OK", "virtual environment", sys.prefix)
    return True


def check_packages():
    missing = [m for m, _ in PACKAGES if importlib.util.find_spec(m) is None]
    fix = ("python3 -m pip install -r requirements.txt" if in_venv()
           else VENV_FIX)
    for module, purpose in PACKAGES:
        if module in missing:
            row("MISSING", module, purpose, fix)
        else:
            row("OK", module, purpose)
    return not missing


def check_chromium():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch().close()
        row("OK", "Chromium", "launches")
    except Exception as e:  # noqa: BLE001 - any failure means not usable
        text = str(e).strip()
        first = text.splitlines()[0] if text else repr(e)
        row("MISSING", "Chromium", first[:120],
            f"{sys.executable} -m playwright install chromium")


def check_https():
    try:
        urllib.request.urlopen("https://osv.dev/", timeout=15).close()
        row("OK", "HTTPS from Python", "reached osv.dev")
    except OSError as e:
        reason = getattr(e, "reason", e)
        if isinstance(e, ssl.SSLError) or isinstance(reason, ssl.SSLError):
            row("MISSING", "HTTPS from Python",
                f"certificate error: {reason}", CERT_FIX)
        else:
            row("MISSING", "HTTPS from Python", f"no connection: {reason}",
                "check the network; the security check looks up "
                "advisories online")


def check_command(name, purpose, fix, required=True):
    if shutil.which(name) is None:
        row("MISSING" if required else "OPTIONAL", name, purpose, fix)
        return False
    _, out = run([name, "--version"])
    first = out.splitlines()[0] if out else ""
    row("OK", name, first or purpose)
    return True


def check_git_identity():
    missing = []
    for key in ("user.name", "user.email"):
        # Any level git would use for a commit outside a repo: system,
        # global or XDG. --global alone misses a system-wide identity.
        code, out = run(["git", "-C", str(pathlib.Path.home()), "config",
                         key])
        if code != 0 or not out:
            missing.append(key)
    if missing:
        row("MISSING", "git name and email", f"not set: {', '.join(missing)}",
            'git config --global user.name "Your Name"; git config '
            '--global user.email "you@archive.org"')
    else:
        row("OK", "git name and email", "set")


def check_gh_auth():
    code, _ = run(["gh", "auth", "status"])
    if code == 0:
        row("OK", "GitHub sign-in", "gh is logged in")
    else:
        row("MISSING", "GitHub sign-in", "gh is not logged in",
            "gh auth login, then gh auth setup-git")


def check_skill():
    sys.path.insert(0, str(HERE))
    try:
        import install
    except ImportError as e:
        row("MISSING", "skill installed", str(e), "python install.py")
        return
    reinstall = f"{sys.executable} install.py"
    record = install.DEST / install.RECORD
    if not install.DEST.exists():
        row("MISSING", "skill installed", str(install.DEST), reinstall)
    elif install.differs(install.SRC, install.DEST):
        row("MISSING", "skill up to date", "installed copy is out of date",
            reinstall)
    elif not record.exists():
        row("MISSING", "skill knows its Python",
            "installed before install.py recorded one", reinstall)
    elif record.read_text(encoding="utf-8").strip() != sys.executable:
        row("MISSING", "skill knows its Python",
            f"it uses {record.read_text(encoding='utf-8').strip()}, "
            "not this one", reinstall)
    else:
        row("OK", "skill installed", f"{install.DEST}, using this Python")


def main():
    if MAC:
        check_command("brew", "installs Python, gh and the rest",
                      "see SETUP.md, step 1")
    python_ok = check_python()
    if python_ok:
        if check_packages():
            check_chromium()
        check_https()
    if check_command("git", "copies explorers to this Mac",
                     "xcode-select --install"):
        check_git_identity()
    if check_command("gh", "opens pull requests", "brew install gh"):
        check_gh_auth()
    check_command("npm", "only for explorers with a package.json",
                  "brew install node, if an explorer you check has a "
                  "package.json", required=False)
    if python_ok:
        check_skill()

    width = max(len(r[1]) for r in rows)
    for status, what, detail, fix in rows:
        print(f"{status:<8} {what:<{width}}  {detail}")
        if fix:
            print(f"{'':<8} {'':<{width}}  -> {fix}")
    missing = [r for r in rows if r[0] == "MISSING"]
    print()
    if missing:
        print(f"{len(missing)} thing(s) to fix. Fix them in the order "
              "listed, then run this again.")
        return 1
    print("Everything the checks need is here.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
