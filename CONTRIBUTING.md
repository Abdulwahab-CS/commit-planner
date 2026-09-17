# Contributing

Thanks for helping! The goal is a skill that stays **simple**: it does the common job
well, and extra behaviour is opt-in through a small set of options.

## Layout

```
skills/commit-planner/
├── SKILL.md                     # instructions the agent follows (keep it short)
├── assets/COMMIT_PLAN.template.md
└── scripts/
    ├── run-pre-commit.sh        # the `pre-commit` / `pre-commit-clean` options
    ├── check_plan.py            # checks COMMIT_PLAN.md before committing
    └── verify.sh                # checks the commits afterwards
```

## Naming options

Name an option after the tool it uses. For a variant, add the tool's own subcommand:
`pre-commit`, then `pre-commit-clean` (runs `pre-commit clean` first). Anyone who knows
the tool understands the option without reading the docs.

## Adding an option

1. Add a row to the **Options** table in `SKILL.md` and a short section under Step 0.
2. Put any logic in a small script in `scripts/`, called from that section.
3. Add the option to the table in `README.md` and a line to `CHANGELOG.md`.

Keep the default path (no options) free of extra tools, and keep the list of options short.

## Testing your change

Try it on a real repository with a few changed and new files:

1. Ask your agent to "plan my commits" (with and without your option).
2. Check that `COMMIT_PLAN.md` groups the files sensibly and passes
   `python3 skills/commit-planner/scripts/check_plan.py`.
3. Say "proceed", then confirm `verify.sh` prints `VERIFIED`.

Use Conventional Commits for your own commits, and bump `version` in both
`.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` when releasing.
