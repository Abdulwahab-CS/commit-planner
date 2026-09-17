# Commit plan

> Temporary review file. Edit it freely, then say "proceed".
> It is never committed. Delete it once the commits are confirmed.

Base: `<base-sha>`

| # | Commit | Files |
|---|---|---|
| 1 | feat(orders): add refund status to order model | 2 |
| 2 | feat(orders): add refund endpoint | 2 |

Run one block at a time. Nothing is pushed.

## 0. Unstage everything

```bash
git reset -q
```

## 1. feat(orders): add refund status to order model

```bash
git add -- orders/models.py orders/migrations/0012_refund_status.py && git commit -F - <<'EOF'
feat(orders): add refund status to order model

Refunds were tracked in a free-text note that reports could not
filter. A status field makes partial refunds queryable.
EOF
```

## 2. feat(orders): add refund endpoint

```bash
git add -- orders/views.py orders/urls.py && git commit -F - <<'EOF'
feat(orders): add refund endpoint
EOF
```

## Verify

```bash
git log --oneline <base-sha>..HEAD && git status --short
git log --reverse --format='%h  author: %an <%ae>  committer: %cn <%ce>' <base-sha>..HEAD
git log --format=%B <base-sha>..HEAD | grep -iE 'co-authored-by|claude|anthropic|assistant|generated with' || echo "no attribution text"
```
