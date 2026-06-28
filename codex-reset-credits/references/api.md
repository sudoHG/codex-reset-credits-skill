# Reset Credits API Reference

Use this reference only when the query script needs maintenance or troubleshooting.

## Endpoint

```text
GET https://chatgpt.com/backend-api/wham/rate-limit-reset-credits
```

This is a read-only ChatGPT backend endpoint observed to return Codex banked reset credits for the authenticated account.

## Required Inputs

- `${CODEX_HOME:-~/.codex}/auth.json`
- `tokens.access_token` or `tokens.accessToken`
- Optional account id from either:
  - JWT payload claim `https://api.openai.com/auth.chatgpt_account_id`
  - `tokens.account_id` / `tokens.accountId`

## Headers

```text
Authorization: Bearer <access_token>
originator: Codex Desktop
OAI-Product-Sku: CODEX
Accept: application/json
ChatGPT-Account-Id: <chatgpt_account_id>
```

## Response Fields

The script handles both snake_case and camelCase:

- `available_count` / `availableCount`
- `credits[].status`
- `credits[].reset_type` / `credits[].resetType`
- `credits[].expires_at` / `credits[].expiresAt`
- `credits[].granted_at` / `credits[].grantedAt`
- `credits[].redeemed_at` / `credits[].redeemedAt`
- `credits[].redeem_started_at` / `credits[].redeemStartedAt`

## Error Interpretation

- `missing_auth`: Codex Desktop login state was not found.
- `invalid_auth_shape`: `auth.json` shape changed or is not readable by this script.
- `missing_access_token`: login state exists but lacks an access token.
- HTTP `401` / `403`: login expired, account mismatch, or endpoint auth rejected.
- HTTP `429`: query rate limited; wait for `Retry-After` if present.
- `invalid_json`: endpoint response shape changed.

