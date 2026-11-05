# Setup

Everything this checker needs on a Mac, and how to keep it up to date.

**The easy way: point Claude at this file.** In Claude Desktop's **Code**
tab, with this repository as the project folder, ask:

> Read SETUP.md and set me up. Run `check_setup.py` first, and ask me before each install.

Claude follows the steps below and runs `check_setup.py` again until
everything is ready. The rest of this page is what it follows, and what
to do yourself if you'd rather.

## Contents

0. [Get this repository](#0-get-this-repository)
1. [The Mac baseline](#1-the-mac-baseline)
2. [Make sure Python is current](#2-make-sure-python-is-current)
3. [The checker's own environment](#3-the-checkers-own-environment)
4. [Check everything](#4-check-everything)
5. [Install the skill](#5-install-the-skill)
6. [Keeping it up to date](#6-keeping-it-up-to-date)
7. [When something goes wrong](#7-when-something-goes-wrong)
8. [For Claude](#8-for-claude)

## What this repository needs

| Software | Version | Why |
|---|---|---|
| Xcode Command Line Tools | any | git and the basic tools everything else depends on |
| Homebrew | any | installs Python and gh |
| Python | **3.10 or newer**; 3.12 or newer recommended | runs the checks. Not Apple's own `/usr/bin/python3` |
| Python packages, in `requirements.txt` | as listed | html5lib, playwright, ruff, bandit, pip-audit, pytest: the tools the checks run |
| Chromium | installed by Playwright | the accessibility check drives it |
| gh, signed in | any | opens pull requests |
| git name and email | set | commits in the explorers you check |
| Node.js / npm | optional | only for an explorer with a `package.json` |

The checker does **not** need the `ia` command-line tool, pipx, jq or GNU
Parallel. The Mac setup guide installs them for other work; they do no
harm here.

## 0. Get this repository

In the **Code** tab, ask:

> Clone `https://github.com/internetarchivecanada/accessibility-security-checker` to `~/projects/accessibility-security-checker`.

Then choose `~/projects/accessibility-security-checker` as the project
folder.

If the app shows **GitHub CLI authentication required**, click **Install
and authenticate**, then **Authorize** in the browser page that opens, and
ask again. This is
[step 4 of Install Claude Code](https://github.com/internetarchivecanada/ia-admin/blob/main/docs/install-claude-code.md#4-point-claude-at-ia-admin)
in ia-admin. "Repository not found" means you are not in the
`internetarchivecanada` organization yet; see
[Get a GitHub account](https://github.com/internetarchivecanada/ia-admin/blob/main/docs/github-account.md).

## 1. The Mac baseline

Two guides cover a Mac from scratch. Do them first, or skip the parts
already done:

- **[Install Claude Code](https://github.com/internetarchivecanada/ia-admin/blob/main/docs/install-claude-code.md)**
  (ia-admin): a Claude account, GitHub membership of
  `internetarchivecanada`, and Claude Desktop.
- **[Mac setup for Claude Code and GitHub](https://docs.google.com/document/d/1ga3XAW06Q3EpkeLxXO_OK1xJHHDo-BEGjL82sfEn1Ao/edit?usp=sharing)**:
  Xcode Command Line Tools, Homebrew, Python, the GitHub CLI and your git
  identity, from a factory-new Mac.

What this checker needs from them, each with the command that confirms
it. Open Terminal with **Cmd + Space**, type `Terminal`, and press
**Return**:

| Need | Install | Confirm |
|---|---|---|
| Xcode Command Line Tools | `xcode-select --install` | `xcode-select -p` prints a path |
| Homebrew | see the Mac setup guide, 1.2 | `brew --version` |
| Python from Homebrew | `brew install python` | `which python3` prints `/opt/homebrew/bin/python3` (or `/usr/local/bin/python3` on an Intel Mac), **not** `/usr/bin/python3` |
| GitHub CLI, signed in | `brew install gh`, then `gh auth login` and `gh auth setup-git` | `gh auth status` says you are logged in |
| git name and email | `git config --global user.name "Your Name"` and `git config --global user.email "you@archive.org"` | `git config --global user.email` prints it |

After installing Homebrew or Python, **close Terminal and open it again**,
so it finds the new commands.

## 2. Make sure Python is current

```bash
brew update
```

```bash
brew upgrade python
```

```bash
python3 --version
```

It should say 3.12 or newer. If `which python3` still says
`/usr/bin/python3`, Terminal is finding Apple's copy: open a new Terminal
window, and if that doesn't help, re-run the PATH lines the Homebrew
installer printed (the Mac setup guide, 1.2).

## 3. The checker's own environment

Homebrew's Python won't install packages into itself (you get an
`externally-managed-environment` error), and that's for the best. The
checker keeps its packages in its own folder, `.venv`, inside this
repository, where they can't disturb anything else.

From this repository's folder:

```bash
cd ~/projects/accessibility-security-checker
```

```bash
python3 -m venv .venv
```

```bash
.venv/bin/python -m pip install --upgrade pip
```

```bash
.venv/bin/python -m pip install -r requirements.txt
```

The last step downloads the Chromium browser the accessibility check
drives, and takes a minute or two:

```bash
.venv/bin/python -m playwright install chromium
```

## 4. Check everything

```bash
.venv/bin/python check_setup.py
```

It checks every item in [What this repository needs](#what-this-repository-needs)
and prints one line each:

- **OK**: present.
- **MISSING**: needed; the line under it says how to fix it.
- **OPTIONAL**: only needed in some cases, which it names.

Fix the `MISSING` lines in the order listed, then run it again, until it
ends with **"Everything the checks need is here."** It's safe to run at
any time and changes nothing.

## 5. Install the skill

```bash
.venv/bin/python install.py
```

This copies the skill to `~/.claude/skills/explorer-checks/`, so Claude
finds it from any folder. It also records which Python ran it, and the
skill runs its checks with that Python. **Always run `install.py` with
`.venv/bin/python`**, so the skill uses the environment that has the
packages.

Setup is done. Next: [START-HERE.md](START-HERE.md), section 4.

## 6. Keeping it up to date

Every few weeks, or when a check reports a `tool:` problem, ask Claude in
this project folder:

> Update the checker: follow SETUP.md, section 6.

Or do it yourself:

```bash
cd ~/projects/accessibility-security-checker
```

```bash
git pull
```

```bash
brew upgrade python
```

```bash
.venv/bin/python -m pip install --upgrade -r requirements.txt
```

```bash
.venv/bin/python -m playwright install chromium
```

```bash
.venv/bin/python check_setup.py
```

If it says the skill is out of date, run `.venv/bin/python install.py`.

**When Homebrew moves Python to a new version** (3.13 to 3.14, say), the
old `.venv` stops working, usually with "No such file or directory" or
"bad interpreter". Rebuild it: delete it, then repeat sections 3 to 5.

```bash
rm -rf .venv
```

## 7. When something goes wrong

| What you see | What to do |
|---|---|
| `check_setup.py` says "found Apple's own copy" | Install Python from Homebrew (section 1), open a new Terminal, and rebuild `.venv` (section 3). |
| `externally-managed-environment` | You ran pip without `.venv/bin/`. Use `.venv/bin/python -m pip …` (section 3). |
| `No module named …` | The packages are in a different Python from the one running. Use `.venv/bin/python` for everything here, then `.venv/bin/python install.py`. |
| "No such file or directory" or "bad interpreter" from `.venv/bin/python` | Homebrew moved Python to a new version. Rebuild `.venv` (section 6). |
| `CERTIFICATE_VERIFY_FAILED` | `brew reinstall ca-certificates python`, then rebuild `.venv`. |
| "Executable doesn't exist" about Chromium | `.venv/bin/python -m playwright install chromium` |
| `gh` says you are not logged in | `gh auth login`, then `gh auth setup-git`. |
| A commit fails with "Please tell me who you are" | Set your git name and email (section 1). |
| `brew`, `gh` or `python3` "command not found" right after installing | Close Terminal and open it again. |
| `/explorer-checks` doesn't come up in Claude | Run `.venv/bin/python install.py`, then start a new Claude session. |

Stuck on something this table doesn't cover? Use the
[feedback form](https://github.com/internetarchivecanada/accessibility-security-checker/issues/new?template=feedback.yml),
and paste what `check_setup.py` prints into its "Setup output" box. The
form opens an issue that only Internet Archive staff can see. Still
leave out passwords and tokens.

## 8. For Claude

When a user asks you to set them up from this file:

- Run `.venv/bin/python check_setup.py` if `.venv` exists, otherwise
  `python3 check_setup.py`, and work from what it reports, not from
  assumptions about the Mac.
- Ask before each install or system change, saying what it installs.
  `brew install`, `xcode-select --install` and the Homebrew installer
  change the system; creating `.venv` and installing into it does not
  reach outside this folder.
- Never ask for, type or store a password or token. `gh auth login` and
  `xcode-select --install` open their own windows, so the user completes
  those.
- Install this repository's packages into `.venv` only, never with
  `--break-system-packages` or `sudo pip`.
- Finish with `.venv/bin/python install.py`, and run `check_setup.py`
  once more to show the user it ends with "Everything the checks need is
  here."
- If a step fails in a way this file doesn't cover, stop and say what
  happened. Don't improvise around it.
