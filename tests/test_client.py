from __future__ import annotations

import json
import unittest
from unittest.mock import patch
from urllib.error import URLError

from github_rep_safe_cleaner.client import GitHubApiError, ReadOnlyGitHubClient, SafetyViolation


class _FakeResponse:
    def __init__(self, payload: object, status: int = 200):
        self._raw = json.dumps(payload).encode("utf-8")
        self.status = status
        self.headers = {
            "X-RateLimit-Limit": "5000",
            "X-RateLimit-Remaining": "4999",
            "X-RateLimit-Reset": "0",
        }

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *_: object) -> bool:
        return False


class ReadOnlyClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = ReadOnlyGitHubClient("test-token", base_url="https://example.invalid")

    def test_blocks_non_read_only_methods(self) -> None:
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            with self.subTest(method=method), self.assertRaises(SafetyViolation):
                self.client.request("/user", method=method)

    def test_blocks_unlisted_endpoint(self) -> None:
        with self.assertRaises(SafetyViolation):
            self.client.request("/repos/demo/repo/actions/secrets")

    def test_allows_expected_read_endpoint_before_network(self) -> None:
        self.client._validate("GET", "/repos/demo/repo/commits")

    def test_retries_transient_connection_reset_and_recovers(self) -> None:
        sleeps: list[float] = []
        retries: list[str] = []
        client = ReadOnlyGitHubClient(
            "test-token",
            base_url="https://example.invalid",
            max_retries=2,
            sleeper=sleeps.append,
            jitter=lambda: 0.5,
            on_retry=retries.append,
        )
        failure = URLError(ConnectionResetError(54, "Connection reset by peer"))
        with patch(
            "github_rep_safe_cleaner.client.urlopen",
            side_effect=[failure, _FakeResponse({"login": "demo-user"})],
        ) as mocked:
            response = client.request("/user")
        self.assertEqual(response.data["login"], "demo-user")
        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(client.retry_events, 1)
        self.assertEqual(len(sleeps), 1)
        self.assertEqual(len(retries), 1)

    def test_exhausted_network_retries_become_github_api_error(self) -> None:
        client = ReadOnlyGitHubClient(
            "test-token",
            base_url="https://example.invalid",
            max_retries=1,
            sleeper=lambda _: None,
            jitter=lambda: 0.5,
        )
        failures = [
            URLError(ConnectionResetError(54, "Connection reset by peer")),
            URLError(ConnectionResetError(54, "Connection reset by peer")),
        ]
        with patch("github_rep_safe_cleaner.client.urlopen", side_effect=failures):
            with self.assertRaisesRegex(GitHubApiError, "after 2 attempts"):
                client.request("/user")

    def test_probe_records_exhausted_network_failure_and_skips_remaining_probes(self) -> None:
        client = ReadOnlyGitHubClient(
            "test-token",
            base_url="https://example.invalid",
            max_retries=0,
        )
        failure = URLError(ConnectionResetError(54, "Connection reset by peer"))
        with patch("github_rep_safe_cleaner.client.urlopen", side_effect=failure) as mocked:
            evidence = client.probe_repository("demo-user/example")
        self.assertTrue(evidence["checked"])
        self.assertEqual(mocked.call_count, 1)
        self.assertEqual(len(evidence["errors"]), 2)
        self.assertIn("remaining probes skipped", evidence["errors"][1])
        self.assertIsNone(evidence["has_commits"])
        self.assertIsNone(evidence["has_releases"])
        self.assertIsNone(evidence["has_issues"])
        self.assertIsNone(evidence["has_pull_requests"])
        self.assertIsNone(evidence["has_branches"])


if __name__ == "__main__":
    unittest.main()
