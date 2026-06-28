# codex-reset-credits-skill

[Simplified Chinese](README.zh-CN.md)

`codex-reset-credits-skill` packages a Codex Skill named `codex-reset-credits`.

It lets Codex query banked Codex reset credits from the local Codex Desktop login state and report available count plus expiration times. The query is local-first and read-only: it reads `${CODEX_HOME:-~/.codex}/auth.json`, calls the ChatGPT backend reset-credit endpoint, and prints only sanitized output.

This project is unofficial and is not affiliated with OpenAI.

## Use With Codex

Send Codex this file:

```text
https://github.com/sudoHG/codex-reset-credits-skill/blob/main/USE_WITH_CODEX.md
```

Then ask:

```text
Check my Codex reset credits and expiration times.
```

Codex should read the runbook, run the script locally, and return a clean summary table.

## Install As A Codex Skill

Copy the Skill folder into your Codex skills directory:

```sh
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R codex-reset-credits "${CODEX_HOME:-$HOME/.codex}/skills/codex-reset-credits"
```

Restart Codex or open a new Codex session. Then ask:

```text
Check how many Codex reset credits I have left and when they expire.
```

## Direct CLI

```sh
python3 codex-reset-credits/scripts/query_reset_credits.py --human
python3 codex-reset-credits/scripts/query_reset_credits.py --json
```

Example `--human` output:

```markdown
Codex reset credits

| Summary | Value |
| --- | --- |
| Available reset credits | `3` |
| Earliest expiration | `2026-07-16 15:51:44 CST` |

| # | Status | Type | Expires local | Expires UTC | ID suffix |
| --- | --- | --- | --- | --- | --- |
| 1 | `available` | `codex_rate_limits` | 2026-07-16 15:51:44 CST | 2026-07-16 07:51:44 UTC | `c60e4307` |
```

## Safety Boundaries

- Do not paste tokens into Codex.
- The script reads local Codex Desktop auth state.
- The script must not print access tokens, full `auth.json`, full account ids, full credit ids, or raw backend responses.
- The script does not redeem reset credits.
- The script does not call mutation or control endpoints.
- The backend endpoint is not a public stable API; auth or response shape may change.

## Validate

```sh
python3 -m unittest discover -s tests -v
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py codex-reset-credits
```

## License

MIT.
