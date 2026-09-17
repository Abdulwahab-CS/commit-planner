# commit-planner

**Turn a messy working tree into clean, reviewable commits, and understand your own
changes along the way.**

An [Agent Skill](https://agentskills.io) for Claude Code, Codex, Cursor, Gemini CLI and
other AI coding agents. It reads your uncommitted changes, groups them into small, focused
commits with [Conventional Commits](https://www.conventionalcommits.org) messages, and
writes the plan to `COMMIT_PLAN.md` for you to review. Nothing is committed until you say
**proceed**, and nothing is ever pushed.

## Why

AI agents change a lot of code, fast, and across many files at once. The usual result is
one big commit called "update stuff" that nobody can review, and a history nobody can
learn from. commit-planner puts a short review step between *code changed* and
*code committed*:

- **You understand what changed.** Seeing your changes grouped by intent is the quickest
  way to review work you, or your agent, just did. You own every commit because you
  approved every one.
- **Reviewers get an easy job.** A pull request made of focused commits can be read
  commit by commit, like chapters, instead of as one wall of diff.
- **History stays useful.** Meaningful commits make `git log`, `git blame`, `git revert`
  and `git bisect` work for you, and consistent messages can generate changelogs and
  release notes automatically.
- **It's consistent.** Every commit follows the same message style, whether the code was
  written by hand or with AI.
- **CI stays green.** The optional `pre-commit` and `ci` checks catch problems before
  you push.

## See it in action

You added a feature: users can archive a project. Six changed files:

```
 M projects/models.py                          # store who archived a project and when
?? projects/migrations/0008_archive_fields.py  # matching database change
 M projects/serializers.py                     # include the archive info in responses
 M projects/views.py                           # handle the archive request
 M projects/urls.py                            # route for it
?? tests/test_archive.py                       # tests for archiving
```

You ask *"plan my commits"* and get three commits:

| # | Commit | Files |
|---|---|---|
| 1 | `feat(projects): add archive fields to project` | `models.py`, `migrations/0008_archive_fields.py` |
| 2 | `feat(projects): add archive endpoint` | `serializers.py`, `views.py`, `urls.py` |
| 3 | `test(projects): cover archiving a project` | `tests/test_archive.py` |

Each commit is one complete idea, and each works on its own.

The data change and its migration belong together, because either one alone leaves the
code and the database out of step. The three API files are individually meaningless (a
route with nothing behind it, a response format nobody returns) but together they are one
working endpoint. And the order follows the dependencies: the data comes first, then what's
built on it.

## A bigger one

You built a password-reset feature. Your working tree looks like this:

```
 M README.md
 M config/settings.py
 M core/middleware.py
 M pyproject.toml
 M users/models.py
 M users/urls.py
 M users/views.py
 M uv.lock
?? templates/emails/password_reset.html
?? tests/users/test_password_reset.py
?? users/migrations/0007_password_reset_token.py
?? users/services/password_reset.py
```

You ask *"plan my commits"* and get this plan:

| # | Commit | Files |
|---|---|---|
| 1 | `build(deps): add itsdangerous for signed tokens` | `pyproject.toml`, `uv.lock` |
| 2 | `feat(users): add password reset token model` | `users/models.py`, `users/migrations/0007_password_reset_token.py` |
| 3 | `feat(users): add password reset service` | `users/services/password_reset.py`, `config/settings.py` |
| 4 | `feat(users): add password reset email template` | `templates/emails/password_reset.html` |
| 5 | `feat(users): add password reset endpoints` | `users/views.py`, `users/urls.py` |
| 6 | `feat(core): rate-limit password reset requests` | `core/middleware.py` |
| 7 | `test(users): cover the password reset flow` | `tests/users/test_password_reset.py` |
| 8 | `docs: document password reset setup` | `README.md` |

Twelve files became eight commits, in dependency order: dependency, model, logic,
template, endpoints, then tests and docs. A body is added only when the *why* isn't
obvious:

```
feat(core): rate-limit password reset requests

Reset emails were an easy way to spam users and probe for accounts.
Requests are now limited to five per hour per IP and per email.
```

## How it works

1. **Reads** your actual diffs, not just file names.
2. **Groups** files by concern, in a dependency-safe order.
3. **Plans**: writes `COMMIT_PLAN.md` with a message and a ready-to-run command per commit,
   then stops.
4. **Commits** after you say "proceed", as you, and verifies the result. It never pushes.

## The plan file: `COMMIT_PLAN.md`

The plan is a temporary review file in your repository root.

- **Review before anything happens.** Read it like a spec: reword a message, move a file
  to another commit, merge or reorder commits. Edit the file or reply in chat, then say
  "proceed".
- **It survives closed sessions.** The plan lives in a file, not only in the chat, so
  nothing is lost if the session ends. A new session picks it up from there.
- **It's never committed.** It is hidden from `git status` (through `.git/info/exclude`)
  and never mentioned in commit messages.
- **Delete it when you're done.** It sits in the repo root on purpose, so you notice it and
  remember to delete it once your commits are confirmed. After that, its job is over.

## Install

**Claude Code (plugin)**

```
/plugin marketplace add Abdulwahab-CS/commit-planner
/plugin install commit-planner@commit-planner
```

**Any agent** (Claude Code, Codex, Cursor, Gemini CLI, Antigravity, ...) via the
[skills CLI](https://skills.sh)

```
npx skills add Abdulwahab-CS/commit-planner
```

**Manual**: copy `skills/commit-planner/` into your agent's skills folder, e.g.
`~/.claude/skills/` for Claude Code.

## Use

Ask *"plan my commits"*, or run `/commit-planner` with optional options:

| Option | Adds |
|---|---|
| *(none)* | Plan and commit, nothing else |
| `pre-commit` | Run the repo's pre-commit hooks on all files first |
| `pre-commit-clean` | Clear the pre-commit hook cache, then run the hooks |
| `ci` | Check what CI enforces beyond the hooks (tests, migrations, ...) |

```
/commit-planner pre-commit ci
```

Then review `COMMIT_PLAN.md`, ask for changes or say **proceed**, and delete the file once
you're happy. When installed as a Claude Code plugin, the command is namespaced:
`/commit-planner:commit-planner`.

## Principles

- **You own the commits.** They are authored and committed with your own git identity,
  with no co-author or tool trailers. You reviewed every commit, so the history reads like
  commits you wrote by hand. If a project requires sign-off or AI disclosure, the
  project's rules come first.
- **Nothing happens without approval.** No commit before "proceed", no push, ever.

## Requirements

git, bash and Python 3. The pre-commit options also require
[pre-commit](https://pre-commit.com).

## Contributing

Ideas and pull requests are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
