# Explorer repositories: before you branch

Most explorers live in `github.com/internetarchivecanada`, and many also run
on the wayback-labs studio. Three hazards, all learned the hard way:

**The remote may not be `origin`.** A studio checkout reaches GitHub
through a remote named `canada`. A laptop clone uses `origin`. Run
`git remote -v` and use whichever points at the GitHub repository.

**`main` can be stale.** People commit straight to the studio, and GitHub
catches up only when someone pushes. Before branching:

```bash
git fetch --all --prune
git log --oneline -1 <remote>/main
```

If the last commit there is old next to the live site's behaviour, or the
README describes features the code lacks, say so to the user before
checking. A report on stale code sends the owners after problems already
fixed.

**Repository names do not always match the studio folder.** `bet`,
`meetings` and `wbm-collections-explorer` differ. The live URL's path is not
proof of the repository name.

## Who owns the repository

The explorer is usually not the user's own. So:

- Ask before the first push to a repository on a run, and never push to
  `main`.
- One branch, `explorer-checks`, and one PR per explorer, updated on every
  re-run.
- Never merge. Never close someone else's PR or delete their branch.

## Generated files

Many explorers build their page data (`data.js`, an index JSON, a SQLite
file) from a pipeline. A finding in generated output is fixed in the
generator. Say that in the recommended fix and name the build script, or
the next build undoes the fix.
