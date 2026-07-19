from __future__ import annotations

import unittest

from github_rep_safe_cleaner.client import ReadOnlyGitHubClient, SafetyViolation


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


if __name__ == "__main__":
    unittest.main()
