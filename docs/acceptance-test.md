# Real-account acceptance test

The v1.0 real-account test established that authentication and inventory work, but transient connection resets aborted deep verification. Version 1.1 must now complete or degrade safely.

1. Update the existing checkout to `agent/read-only-repo-auditor`.
2. Activate the Python 3.11+ virtual environment and reinstall editable mode.
3. Run `python scripts/check_safety.py` and `python -m unittest discover -s tests -v`.
4. Use the existing GitHub CLI authentication or another read-capable local credential.
5. Run `repo-safe-cleaner scan --output artifacts/runs/first-real-scan`.
6. If the process is interrupted by an external event, rerun the exact same scan command **without deleting the output directory**. Successful deep probes must show as `Resume ...`.
7. Confirm transient connection resets produce `Retry x/5 ...` instead of an uncaught `urlopen` exception.
8. Open `artifacts/runs/first-real-scan/review.html`.
9. Verify that public and private repositories are both present, filters work, decisions persist, and `decisions.json` exports.
10. Review every `DELETE_CANDIDATE`; do not treat the label as authorization.
11. Return `report.md`, `manifest.json`, the final `retry_events` value, and any misclassified repository names or errors.

Success means the scan reaches report generation without any repository mutation. Persistent failures for an individual repository may appear as explicit evidence errors and `MANUAL_REVIEW`; they must not abort the full scan or produce `DELETE_CANDIDATE`.
