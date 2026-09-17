#!/usr/bin/env python3
"""Check COMMIT_PLAN.md before committing.

- every changed file is in exactly one commit
- commit subjects follow `type(scope): summary`
- no attribution text, identity overrides, hook skipping or pushing
- COMMIT_PLAN.md itself is never committed or mentioned in a message
- the plan's base is still HEAD

Also adds COMMIT_PLAN.md to .git/info/exclude so it never shows up in `git status`.
Usage: python3 check_plan.py [path/to/COMMIT_PLAN.md]
"""
import os
import re
import shlex
import subprocess
import sys

PLAN = "COMMIT_PLAN.md"
SUBJECT = re.compile(
    r"^(feat|fix|refactor|perf|test|docs|style|build|ci|chore|revert)(\([\w./-]+\))?!?: \S.*$")
ATTRIBUTION = re.compile(
    os.environ.get("AUTHORSHIP_PATTERN",
                   r"co-authored-by|claude|anthropic|assistant|generated with"), re.I)
COMMIT_LINE = re.compile(r"^git add -- (.+?) && git commit(.*?) -F - <<'EOF'$")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout


def changed_files():
    out = git("status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames")
    files = {entry[3:] for entry in out.split("\0") if len(entry) > 3}
    files.discard(PLAN)
    return files


def parse_commits(lines):
    """Return [(files, flags, message)] for each commit block in the plan."""
    commits, i = [], 0
    while i < len(lines):
        match = COMMIT_LINE.match(lines[i].strip())
        i += 1
        if not match:
            continue
        body = []
        while i < len(lines) and lines[i].strip() != "EOF":
            body.append(lines[i])
            i += 1
        i += 1
        files = [os.path.normpath(f) for f in shlex.split(match.group(1))]
        commits.append((files, match.group(2), "\n".join(body).strip()))
    return commits


def check(text):
    errors, warnings = [], []
    commits = parse_commits(text.splitlines())
    if not commits:
        errors.append("no commit blocks found (use: git add -- <files> && git commit -F - <<'EOF')")

    commit_lines = re.findall(r"^\s*git (?:add|commit)\b.*$", text, re.M)
    if len(commit_lines) != len(commits):
        errors.append("every commit must be one line: git add -- <files> && git commit -F - <<'EOF'")
    if re.search(r"^\s*git push\b", text, re.M):
        errors.append("the plan must not push")
    if "<base-sha>" in text:
        errors.append("fill in <base-sha> with the output of: git rev-parse HEAD")

    base = re.search(r"Base:\s*`?([0-9a-f]{7,40})", text)
    head = git("rev-parse", "--verify", "-q", "HEAD").strip()
    if not base and head:
        errors.append("missing 'Base: <sha>' line")
    elif head and not head.startswith(base.group(1)):
        errors.append(f"plan base {base.group(1)[:10]} is not HEAD {head[:10]}: the plan is stale")
    if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode == 1 \
            and "git reset" not in text:
        errors.append("files are staged: start the plan with `git reset -q`")

    changed, owner = changed_files(), {}
    for n, (files, flags, message) in enumerate(commits, 1):
        for bad in ("--author", "--no-verify", "--amend", " -a", " -n", "--all"):
            if bad in f" {flags}":
                errors.append(f"commit {n}: '{bad.strip()}' is not allowed")
        for f in files:
            if f == PLAN:
                errors.append(f"commit {n}: {PLAN} is a temporary review file, never commit it")
                continue
            owner.setdefault(f, []).append(n)
            if f not in changed:
                errors.append(f"commit {n}: {f} has no changes")
        subject = message.split("\n", 1)[0]
        if not SUBJECT.match(subject):
            errors.append(f"commit {n}: subject should be 'type(scope): summary': {subject!r}")
        if subject.endswith("."):
            errors.append(f"commit {n}: subject ends with a period")
        if len(subject) > 72:
            errors.append(f"commit {n}: subject is {len(subject)} chars (max 72)")
        elif len(subject) > 50:
            warnings.append(f"commit {n}: subject is {len(subject)} chars (aim for 50)")
        if "\n" in message and message.split("\n")[1].strip():
            errors.append(f"commit {n}: leave a blank line after the subject")
        if PLAN.lower() in message.lower() or "commit plan" in message.lower():
            errors.append(f"commit {n}: don't mention the commit plan in the message")
        hit = ATTRIBUTION.search(message)
        if hit:
            errors.append(f"commit {n}: remove attribution text {hit.group(0)!r}")

    for f, numbers in sorted(owner.items()):
        if len(numbers) > 1:
            errors.append(f"{f} is in more than one commit: {numbers}")
    for f in sorted(changed - set(owner)):
        errors.append(f"{f} is not in any commit")
    return commits, errors, warnings


def hide_plan_from_git_status():
    exclude = git("rev-parse", "--git-path", "info/exclude").strip()
    os.makedirs(os.path.dirname(exclude) or ".", exist_ok=True)
    current = open(exclude).read() if os.path.exists(exclude) else ""
    if f"/{PLAN}" not in current.split("\n"):
        with open(exclude, "a") as fh:
            fh.write(("" if current.endswith("\n") or not current else "\n") + f"/{PLAN}\n")


def main():
    plan_path = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else PLAN)
    top = git("rev-parse", "--show-toplevel").strip()
    if not top:
        sys.exit("Not inside a git repository.")
    os.chdir(top)
    if not os.path.isfile(plan_path):
        sys.exit(f"{plan_path} not found.")

    commits, errors, warnings = check(open(plan_path, encoding="utf-8").read())
    hide_plan_from_git_status()

    for n, (files, _, message) in enumerate(commits, 1):
        print(f"{n}. {message.split(chr(10), 1)[0]}  ({len(files)} files)")
    for w in warnings:
        print(f"  warning: {w}")
    for e in errors:
        print(f"  error: {e}")
    print("PLAN OK" if not errors else f"PLAN HAS {len(errors)} ERROR(S)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
