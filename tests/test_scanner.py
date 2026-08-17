from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from github_rep_safe_cleaner.scanner import scan_account


def _repo_payload(*, updated_at: str = "2026-08-17T00:00:00Z") -> dict[str, object]:
    return {
        "id": 1,
        "name": "empty-demo",
        "full_name": "demo-user/empty-demo",
        "html_url": "https://github.com/demo-user/empty-demo",
        "visibility": "public",
        "private": False,
        "fork": False,
        "archived": False,
        "disabled": False,
        "size": 0,
        "default_branch": "main",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": updated_at,
        "pushed_at": None,
    }


class _FakeClient:
    def __init__(self, payload: dict[str, object], *, with_error: bool = False):
        self.payload = payload
        self.with_error = with_error
        self.probe_calls: list[str] = []

    def authenticated_login(self) -> str:
        return "demo-user"

    def list_owned_repositories(self) -> list[dict[str, object]]:
        return [self.payload]

    def probe_repository(self, full_name: str) -> dict[str, object]:
        self.probe_calls.append(full_name)
        errors = ["has_commits: transient failure"] if self.with_error else []
        return {
            "checked": True,
            "has_commits": None if errors else False,
            "has_releases": False,
            "has_issues": False,
            "has_pull_requests": False,
            "has_branches": False,
            "errors": errors,
        }


class ScannerCheckpointTests(unittest.TestCase):
    def test_reuses_successful_checkpoint_when_repository_fingerprint_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint = Path(tmp) / "checkpoint.json"
            first = _FakeClient(_repo_payload())
            _, first_repositories = scan_account(first, checkpoint_path=checkpoint)
            self.assertEqual(first.probe_calls, ["demo-user/empty-demo"])
            self.assertTrue(first_repositories[0].deep.checked)
            self.assertTrue(checkpoint.exists())

            second = _FakeClient(_repo_payload())
            _, second_repositories = scan_account(second, checkpoint_path=checkpoint)
            self.assertEqual(second.probe_calls, [])
            self.assertTrue(second_repositories[0].deep.checked)

    def test_reprobes_when_repository_changed_or_previous_probe_had_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint = Path(tmp) / "checkpoint.json"
            failed = _FakeClient(_repo_payload(), with_error=True)
            scan_account(failed, checkpoint_path=checkpoint)
            self.assertEqual(len(failed.probe_calls), 1)

            retry = _FakeClient(_repo_payload())
            scan_account(retry, checkpoint_path=checkpoint)
            self.assertEqual(len(retry.probe_calls), 1)

            changed = _FakeClient(_repo_payload(updated_at="2026-08-18T00:00:00Z"))
            scan_account(changed, checkpoint_path=checkpoint)
            self.assertEqual(len(changed.probe_calls), 1)

            payload = json.loads(checkpoint.read_text(encoding="utf-8"))
            self.assertEqual(payload["repositories"]["demo-user/empty-demo"]["updated_at"], "2026-08-18T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
