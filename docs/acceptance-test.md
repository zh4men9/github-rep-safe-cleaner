# Real-account acceptance test

This is the only remaining manual validation stage.

1. Clone the repository after the implementation PR is available.
2. Create and activate a Python 3.11+ virtual environment.
3. Install with `python -m pip install -e .`.
4. Run `python scripts/check_safety.py` and `python -m unittest discover -s tests -v`.
5. Ensure GitHub CLI is authenticated, or set a read-capable `GH_TOKEN` without placing it in the repository.
6. Run `repo-safe-cleaner scan --output artifacts/runs/first-real-scan`.
7. Open `artifacts/runs/first-real-scan/review.html`.
8. Verify that public and private repositories are both present, filters work, decisions persist, and `decisions.json` exports.
9. Review every `DELETE_CANDIDATE`; do not treat the label as authorization.
10. Return `report.md`, `manifest.json`, and any misclassified repository names or errors for the next iteration.

Success means the scan completes without any repository mutation, reports include both visibility classes, and candidate evidence is understandable enough for one-by-one manual decisions.
