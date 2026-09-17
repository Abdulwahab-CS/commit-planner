---
name: commit-planner
description: Plans small, focused git commits with Conventional Commits messages from uncommitted changes. Writes COMMIT_PLAN.md for review, commits on "proceed", never pushes. Use when the user wants to commit, split, group or tidy changes, or asks for commit messages. Options - pre-commit, pre-commit-clean, ci.
license: MIT
compatibility: Requires git, bash and Python 3. The pre-commit options require pre-commit.
---

# Commit Planner

Turn uncommitted changes into a short series of focused commits. Plan first, commit only
after the user approves.

## Options

The user can add these words to the request, e.g. `/commit-planner pre-commit ci` or "plan
my commits with pre-commit". With no options, go straight to Step 1.

| Option | What it adds |
|---|---|
| `pre-commit` | Run the repo's pre-commit hooks on all files before planning, at the versions pinned in `.pre-commit-config.yaml`. |
| `pre-commit-clean` | Same, but run `pre-commit clean` first to clear the hook cache. Use when hooks behave differently than in CI. |
| `ci` | Read the CI config and check what it enforces beyond the hooks (tests, migrations, ...), so the commits won't fail CI. |

If the repo has a `.pre-commit-config.yaml` and no pre-commit option was requested,
mention in the final summary that the `pre-commit` option exists.

`$SKILL` means this skill's folder. Run all commands from the repository root.

## Rules

- **The user owns the commits.** Use plain `git commit`, so author and committer come from
  the user's git config. No `Co-authored-by` or tool trailers, no mention of AI or tools
  in messages, no `--author` or identity overrides. The user reviews every commit, so the
  history should read like carefully hand-written commits. If the project requires
  something else (e.g. `Signed-off-by` via `git commit -s`, or AI disclosure per its
  CONTRIBUTING guide), follow the project.
- **Nothing is committed before the user says "proceed".** Never push. Never discard
  changes.
- **`COMMIT_PLAN.md` is a temporary review file, not part of the change.** Never stage or
  commit it, and never mention it in commit messages. Don't delete it either; the user
  deletes it once the commits are confirmed.
- **Base every message on the diff**, never on file names alone.
- **Never skip hooks** (`--no-verify`) and never run `pre-commit autoupdate`, because it
  changes the pinned hook versions.

## Step 0: Options (only when requested)

**pre-commit** / **pre-commit-clean**

```bash
bash "$SKILL/scripts/run-pre-commit.sh"            # pre-commit
bash "$SKILL/scripts/run-pre-commit.sh" --clean    # pre-commit-clean
```

This installs hooks at the versions pinned in `.pre-commit-config.yaml` and runs them on
all files, new files included, until they pass. Then act on the exit code:

- `0`: all clean, continue.
- `1`: hook errors remain in the user's files. Fix them, then run it again.
- `2`: setup problem, e.g. pre-commit is missing or hooks failed to install. Report it and
  stop.
- `3`: hooks changed files the user never touched. Stop, show the list, and ask whether to
  revert them or keep them as a separate first commit. Never mix them into feature commits.

**ci**

Read the CI config (`.github/workflows/`, `.gitlab-ci.yml`, ...). Report what it enforces
that the hooks don't cover, such as tests, type checks, `makemigrations --check` or
lockfile checks, and run the quick ones locally. If CI runs pre-commit, confirm it uses the
same config and Python version and doesn't run `autoupdate`. Note anything you couldn't
check at the top of the plan.

## Step 1: Inspect

```bash
git status --short --untracked-files=all
git diff HEAD --stat
git diff HEAD -- <file>     # for any file whose purpose isn't obvious
git log --oneline -15       # match the repo's existing message style and scopes
```

New (untracked) files don't appear in `git diff`, so read them directly. Ignore
`COMMIT_PLAN.md` if it already exists from an earlier run.

## Step 2: Group

One concern per commit, ordered so each commit works on its own:

data model + migrations → config → data access → business logic → templates/assets →
background jobs → API/views → cross-cutting refactors → tests

Skip what doesn't apply and adapt the order to the project. Put a modified file in the
commit of the feature that changed it. Use whole files only, with no partial staging; a
file that mixes concerns goes into its best-fit commit. Every changed file appears in
exactly one commit.

Messages:

- Subject: `type(scope): summary`. Use the imperative ("add", not "added"), lowercase,
  at most 50 characters, no trailing period. Types: `feat`, `fix`, `refactor`, `perf`,
  `test`, `docs`, `style`, `build`, `ci`, `chore`.
- Add a body only when the reason isn't obvious from the subject. Wrap it at 72 columns,
  explain why, and don't list files.

## Step 3: Write the plan and stop

1. Write `COMMIT_PLAN.md` in the repo root, following `$SKILL/assets/COMMIT_PLAN.template.md`.
   Commit blocks use `git commit -F - <<'EOF'`, so messages are passed exactly as written.
2. Check it: `python3 "$SKILL/scripts/check_plan.py"`. Fix the plan until it prints
   `PLAN OK`. The check also hides the plan from `git status` through `.git/info/exclude`,
   so it can't be committed by accident.
3. **Stop.** Reply with one line per commit and wait for "proceed".

If the user gives feedback, whether in chat or by editing `COMMIT_PLAN.md` directly
(rewording messages, moving files between commits, reordering), update the plan, check it
again, and stop again. If a new session starts and `COMMIT_PLAN.md` exists, read it and
continue from it.

## Step 4: Commit (only after "proceed")

Run `check_plan.py` once more, then run the plan's blocks in order, exactly as written. If
a hook changes files during a commit, run that same block one more time. If it still fails,
stop and report. Do not push.

## Step 5: Verify

```bash
bash "$SKILL/scripts/verify.sh" <base-sha-from-the-plan>
```

Show the output to the user and remind them to delete `COMMIT_PLAN.md` once they're happy
with the commits.
