from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from github_rep_safe_cleaner.classify import assess_all
from github_rep_safe_cleaner.models import DeepEvidence, RepositoryRecord
from github_rep_safe_cleaner.report import write_run

FIXTURES = Path(__file__).parent / "fixtures"


class ReportTests(unittest.TestCase):
    def test_writes_complete_run(self) -> None:
        payload = json.loads((FIXTURES / "repos.json").read_text(encoding="utf-8"))
        evidence = json.loads((FIXTURES / "evidence.json").read_text(encoding="utf-8"))
        repos = [RepositoryRecord.from_api(item) for item in payload]
        for repo in repos:
            if repo.full_name in evidence:
                repo.deep = DeepEvidence(**evidence[repo.full_name])
        assessments = assess_all(repos, now=datetime(2026, 7, 19, tzinfo=UTC))
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_run(Path(tmp), owner="demo-user", assessments=assessments)
            for path in paths.values():
                self.assertTrue(path.exists(), path)
            inventory = json.loads(paths["inventory"].read_text(encoding="utf-8"))
            self.assertTrue(inventory["safety"]["read_only"])
            self.assertFalse(inventory["safety"]["performs_repository_deletion"])
            review = paths["review"].read_text(encoding="utf-8")
            self.assertIn("DELETE_MANUALLY", review)
            self.assertNotIn("fetch(", review)


if __name__ == "__main__":
    unittest.main()
