# Use With Codex: Query Codex Reset Credits

This file is an instruction runbook for Codex. Use it when a user gives this link and asks to query Codex reset credits, reset opportunities, reset count, or expiration times.

## Goal

Return the user's current banked Codex reset credits:

- available count
- each available credit status
- reset type
- expiration time in the user's local timezone output by the script

## Safety Rules

- Do not ask the user to paste tokens.
- Do not print or summarize access tokens.
- Do not print the full `auth.json`.
- Do not print full account ids.
- Do not print full credit ids; use only the script's `id_suffix` if needed.
- Do not write raw backend responses to the workspace.
- Do not redeem credits or call mutation/control endpoints.
- Treat HTTP 401/403 as login/auth issues, not as proof that no credits exist.

## How To Run

First locate `query_reset_credits.py`.

If this repository is available locally, run:

```sh
python3 codex-reset-credits/scripts/query_reset_credits.py --json
```

If the user gave a GitHub URL to this file, derive the raw script URL from the same repository and branch:

```text
https://github.com/<owner>/<repo>/blob/<branch>/USE_WITH_CODEX.md
-> https://raw.githubusercontent.com/<owner>/<repo>/<branch>/codex-reset-credits/scripts/query_reset_credits.py
```

Download the script to a temporary path outside the user's project and run it:

```sh
tmp_script="$(mktemp -t codex-reset-credits.XXXXXX.py)"
curl -fsSL "<raw-script-url>" -o "$tmp_script"
python3 "$tmp_script" --json
rm -f "$tmp_script"
```

Use `--json` when Codex will parse the result. Use `--human` only when a human wants terminal-readable output.

## How To Answer

If `ok` is true, answer concisely in the user's language with a clean Markdown summary:

```markdown
查到了。你当前有 `<available_count>` 个可用 Codex 重置机会。

最早到期：`<first available_credits[].expires_at.time_local>`

| # | 状态 | 类型 | 到期时间 | UTC |
| --- | --- | --- | --- | --- |
| 1 | `available` | `codex_rate_limits` | 2026-07-16 15:51:44 CST | 2026-07-16 07:51:44 UTC |
```

Do not wrap the table in a code block in the final answer. Use `id_suffix` only if the user needs to distinguish records. Mention that the result is sanitized only when useful.

If `ok` is false, report the error code and the practical next step:

- `missing_auth`: open Codex Desktop and log in.
- `missing_access_token` or `invalid_auth_shape`: refresh/relogin Codex Desktop.
- HTTP `401` / `403`: login is expired or account id is rejected; relogin Codex Desktop.
- HTTP `429`: wait for `retry_after` if present, otherwise retry later.
- `invalid_json`: backend response shape changed; inspect the endpoint behavior without exposing secrets.
