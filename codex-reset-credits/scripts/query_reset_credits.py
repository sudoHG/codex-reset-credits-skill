#!/usr/bin/env python3
"""Read-only Codex banked reset credit query.

The script reads the local Codex Desktop auth file, calls the ChatGPT backend
reset-credit endpoint, and prints sanitized output only.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover - Python without zoneinfo.
    ZoneInfo = None  # type: ignore


DEFAULT_ENDPOINT = "https://chatgpt.com/backend-api/wham/rate-limit-reset-credits"
CHATGPT_ACCOUNT_ID_CLAIM = "https://api.openai.com/auth"


def pick(dictionary: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if isinstance(dictionary, dict) and dictionary.get(key) not in (None, ""):
            return dictionary[key]
    return None


def decode_base64url(value: str) -> bytes:
    value = value + "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode(value.encode("utf-8"))


def account_id_from_access_token(access_token: str) -> Optional[str]:
    try:
        jwt_parts = access_token.split(".")
        if len(jwt_parts) < 2:
            return None
        jwt_payload = json.loads(decode_base64url(jwt_parts[1]))
        openai_auth = jwt_payload.get(CHATGPT_ACCOUNT_ID_CLAIM)
        if isinstance(openai_auth, dict):
            return openai_auth.get("chatgpt_account_id")
    except Exception:
        return None
    return None


def parse_datetime(value: Any) -> Optional[datetime]:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        timestamp = float(value) / 1000 if float(value) > 10_000_000_000 else float(value)
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)

    text = str(value).strip()
    if text.isdigit():
        timestamp = float(text) / 1000 if len(text) > 10 else float(text)
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)

    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text)
    except Exception:
        return None


def format_datetime(value: Any, timezone_name: str) -> Optional[Dict[str, str]]:
    dt = parse_datetime(value)
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if ZoneInfo:
        local_tz = ZoneInfo(timezone_name)
    else:
        local_tz = timezone.utc
    local = dt.astimezone(local_tz)
    return {
        "date_local": local.strftime("%Y-%m-%d"),
        "time_local": local.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "time_utc": dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


def default_auth_path() -> str:
    codex_home = os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex")
    return os.path.join(os.path.expanduser(codex_home), "auth.json")


def load_auth(auth_path: str) -> Dict[str, Any]:
    with open(auth_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("invalid_auth_shape")
    return data


def build_headers(access_token: str, account_id: Optional[str]) -> Dict[str, str]:
    headers = {
        "Authorization": "Bearer " + access_token,
        "originator": "Codex Desktop",
        "OAI-Product-Sku": "CODEX",
        "Accept": "application/json",
        "User-Agent": "codex-reset-credit-readonly/1.0",
    }
    if account_id:
        headers["ChatGPT-Account-Id"] = account_id
    return headers


def request_reset_credits(endpoint: str, headers: Dict[str, str], timeout: int) -> Dict[str, Any]:
    request = urllib.request.Request(endpoint, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        status_code = response.status
        response_body = response.read()
    try:
        data = json.loads(response_body)
    except Exception as error:
        raise ValueError("invalid_json") from error
    if not isinstance(data, dict):
        raise ValueError("invalid_json")
    return {"status_code": status_code, "data": data}


def sanitize_response(data: Dict[str, Any], status_code: int, timezone_name: str) -> Dict[str, Any]:
    credits = data.get("credits") if isinstance(data, dict) else []
    if not isinstance(credits, list):
        credits = []

    sanitized_credits: List[Dict[str, Any]] = []
    for credit in credits:
        if not isinstance(credit, dict):
            continue
        status = pick(credit, "status") or "unknown"
        expires_at = pick(credit, "expires_at", "expiresAt")
        sanitized_credits.append(
            {
                "id_suffix": str(pick(credit, "id") or "")[-8:],
                "status": status,
                "reset_type": pick(credit, "reset_type", "resetType") or "unknown",
                "expires_at": format_datetime(expires_at, timezone_name),
                "granted_at": format_datetime(pick(credit, "granted_at", "grantedAt"), timezone_name),
                "redeemed_at": format_datetime(pick(credit, "redeemed_at", "redeemedAt"), timezone_name),
                "redeem_started_at": format_datetime(
                    pick(credit, "redeem_started_at", "redeemStartedAt"), timezone_name
                ),
            }
        )

    sanitized_credits.sort(
        key=lambda item: (
            item["expires_at"]["time_utc"] if item.get("expires_at") else "9999",
            item["id_suffix"],
        )
    )
    available_credits = [
        item for item in sanitized_credits if str(item["status"]).lower() == "available"
    ]

    available_count = pick(data, "available_count", "availableCount")
    try:
        available_count = int(available_count)
    except Exception:
        available_count = len(available_credits)

    return {
        "ok": True,
        "status": status_code,
        "queried_at": format_datetime(datetime.now(timezone.utc).isoformat(), timezone_name),
        "available_count": available_count,
        "available_credits": available_credits,
        "all_credit_count": len(sanitized_credits),
    }


def error_payload(error: str, **fields: Any) -> Dict[str, Any]:
    payload = {"ok": False, "error": error}
    payload.update(fields)
    return payload


def query(auth_path: str, endpoint: str, timeout: int, timezone_name: str) -> Dict[str, Any]:
    if not os.path.exists(auth_path):
        return error_payload("missing_auth", auth_path=auth_path)

    try:
        auth_json = load_auth(auth_path)
    except ValueError:
        return error_payload("invalid_auth_shape")
    except Exception as error:
        return error_payload(type(error).__name__, message=str(error))

    tokens = auth_json.get("tokens") if isinstance(auth_json, dict) else None
    if not isinstance(tokens, dict):
        return error_payload("invalid_auth_shape")

    access_token = pick(tokens, "access_token", "accessToken")
    account_id = pick(tokens, "account_id", "accountId")
    if not access_token:
        return error_payload("missing_access_token")

    account_id = account_id_from_access_token(str(access_token)) or account_id
    headers = build_headers(str(access_token), str(account_id) if account_id else None)

    try:
        response = request_reset_credits(endpoint, headers, timeout)
    except urllib.error.HTTPError as error:
        return error_payload(
            "http_error",
            status=error.code,
            retry_after=error.headers.get("Retry-After"),
        )
    except ValueError as error:
        return error_payload(str(error))
    except Exception as error:
        return error_payload(type(error).__name__, message=str(error))

    return sanitize_response(response["data"], response["status_code"], timezone_name)


def human_lines(payload: Dict[str, Any]) -> Iterable[str]:
    if not payload.get("ok"):
        yield "Codex reset credits query failed"
        yield ""
        yield "| Field | Value |"
        yield "| --- | --- |"
        yield "| Error | `" + str(payload.get("error", "unknown")) + "` |"
        if payload.get("status"):
            yield "| HTTP status | `" + str(payload["status"]) + "` |"
        if payload.get("retry_after"):
            yield "| Retry-After | `" + str(payload["retry_after"]) + "` |"
        return

    credits = payload.get("available_credits") or []
    earliest = None
    if credits:
        earliest_dt = credits[0].get("expires_at") or {}
        earliest = earliest_dt.get("time_local")

    yield "Codex reset credits"
    yield ""
    yield "| Summary | Value |"
    yield "| --- | --- |"
    yield "| Available reset credits | `" + str(payload.get("available_count", 0)) + "` |"
    if earliest:
        yield "| Earliest expiration | `" + str(earliest) + "` |"
    if payload.get("queried_at"):
        yield "| Queried at | `" + str(payload["queried_at"].get("time_local")) + "` |"

    if not credits:
        yield ""
        yield "No available reset credits were returned."
        return

    yield ""
    yield "| # | Status | Type | Expires local | Expires UTC | ID suffix |"
    yield "| --- | --- | --- | --- | --- | --- |"
    for index, credit in enumerate(credits, 1):
        expires_at = credit.get("expires_at") or {}
        yield (
            "| "
            + str(index)
            + " | `"
            + str(credit.get("status"))
            + "` | `"
            + str(credit.get("reset_type"))
            + "` | "
            + str(expires_at.get("time_local"))
            + " | "
            + str(expires_at.get("time_utc"))
            + " | `"
            + str(credit.get("id_suffix"))
            + "` |"
        )


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query Codex banked reset credits.")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="Print sanitized JSON output. Default.")
    output.add_argument("--human", action="store_true", help="Print a compact human-readable summary.")
    parser.add_argument("--auth-path", default=default_auth_path(), help="Path to Codex auth.json.")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="Reset credits endpoint.")
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds.")
    parser.add_argument("--timezone", default="Asia/Shanghai", help="Timezone for local display.")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    payload = query(args.auth_path, args.endpoint, args.timeout, args.timezone)
    if args.human:
        print("\n".join(human_lines(payload)))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
