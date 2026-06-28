import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "codex-reset-credits"
    / "scripts"
    / "query_reset_credits.py"
)


spec = importlib.util.spec_from_file_location("query_reset_credits", SCRIPT_PATH)
query_reset_credits = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(query_reset_credits)


class QueryResetCreditsTests(unittest.TestCase):
    def test_sanitize_response_uses_available_count_and_sorts(self):
        data = {
            "available_count": 2,
            "credits": [
                {
                    "id": "credit-later-abcdef12",
                    "status": "available",
                    "reset_type": "codex_rate_limits",
                    "expires_at": "2030-01-03T00:00:00Z",
                },
                {
                    "id": "credit-earlier-12345678",
                    "status": "available",
                    "reset_type": "codex_rate_limits",
                    "expires_at": "2030-01-02T00:00:00Z",
                },
            ],
        }

        payload = query_reset_credits.sanitize_response(data, 200, "Asia/Shanghai")

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["available_count"], 2)
        self.assertEqual(payload["available_credits"][0]["id_suffix"], "12345678")
        self.assertEqual(
            payload["available_credits"][0]["expires_at"]["time_local"],
            "2030-01-02 08:00:00 CST",
        )

    def test_query_never_exposes_access_token_in_output(self):
        fake_response = {
            "credits": [
                {
                    "id": "full-secret-credit-id",
                    "status": "available",
                    "resetType": "codex_rate_limits",
                    "expiresAt": "2030-01-02T07:30:00Z",
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            auth_path = Path(tmpdir) / "auth.json"
            auth_path.write_text(
                json.dumps({"tokens": {"access_token": "secret-token", "account_id": "acct"}}),
                encoding="utf-8",
            )

            with mock.patch.object(
                query_reset_credits,
                "request_reset_credits",
                return_value={"status_code": 200, "data": fake_response},
            ):
                payload = query_reset_credits.query(
                    str(auth_path),
                    "https://example.invalid",
                    1,
                    "Asia/Shanghai",
                )

        rendered = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn("secret-token", rendered)
        self.assertNotIn("full-secret-credit-id", rendered)
        self.assertIn("redit-id", rendered)

    def test_missing_auth_is_clear(self):
        payload = query_reset_credits.query(
            "/tmp/definitely-missing-codex-auth.json",
            "https://example.invalid",
            1,
            "Asia/Shanghai",
        )

        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"], "missing_auth")

    def test_human_output_is_markdown_summary(self):
        payload = {
            "ok": True,
            "queried_at": {"time_local": "2030-01-01 08:00:00 CST"},
            "available_count": 1,
            "available_credits": [
                {
                    "id_suffix": "12345678",
                    "status": "available",
                    "reset_type": "codex_rate_limits",
                    "expires_at": {
                        "time_local": "2030-01-02 08:00:00 CST",
                        "time_utc": "2030-01-02 00:00:00 UTC",
                    },
                }
            ],
        }

        output = "\n".join(query_reset_credits.human_lines(payload))

        self.assertIn("| Summary | Value |", output)
        self.assertIn("| Available reset credits | `1` |", output)
        self.assertIn("| # | Status | Type | Expires local | Expires UTC | ID suffix |", output)
        self.assertIn("| 1 | `available` | `codex_rate_limits` |", output)


if __name__ == "__main__":
    unittest.main()
