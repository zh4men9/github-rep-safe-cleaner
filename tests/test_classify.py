from __future__ import annotations

import json
import unittest
from datetime import UTC, datetime
from pathlib import Path

from github_rep_safe_cleaner.classify import assess_all, build_duplicate_groups, normalize_name
from github_rep_safe_cleaner.models import DeepEvidence, RepositoryRecord

FIXTURES = Path(__file__).parent / "fixtures"


class ClassificationTests(unittest.TestCase):
    def load(self) -> list[RepositoryRecord]:
        payload = json.loads((FIXTURES / "repos.json").read_text(encoding="utf-8"))
        evidence = json.loads((FIXTURES / "evidence.json").read_text(encoding="utf-8"))
        repos = [RepositoryRecord.from_api(item) for item in payload]
        for repo in repos:
            if repo.full_name in evidence:
                repo.deep = DeepEvidence(**evidence[repo.full_name])
        return repos

    def test_normalizes_common_copy_suffixes(self) -> None:
        self.assertEqual(normalize_name("chat-app-1"), normalize_name("chat-app"))
        self.assertEqual(normalize_name("project_backup"), normalize_name("project"))

    def test_detects_duplicate_group(self) -> None:
        groups = build_duplicate_groups(self.load())
        self.assertIn("chatapp", groups)
        self.assertEqual(len(groups["chatapp"]), 2)

    def test_only_verified_empty_repo_becomes_delete_candidate(self) -> None:
        items = assess_all(self.load(), now=datetime(2026, 7, 19, tzinfo=UTC))
        by_name = {item.repository.full_name: item for item in items}
        self.assertEqual(by_name["demo-user/empty-demo"].category, "DELETE_CANDIDATE")
        self.assertEqual(by_name["demo-user/chat-app-1"].category, "MANUAL_REVIEW")
        self.assertEqual(by_name["demo-user/old-fork"].category, "MANUAL_REVIEW")
        self.assertEqual(by_name["demo-user/research-tool"].category, "KEEP")


if __name__ == "__main__":
    unittest.main()
