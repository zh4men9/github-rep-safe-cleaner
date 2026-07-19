# github-rep-safe-cleaner

Version 0.5 adds public/private owned-repository inventory, candidate-targeted deep read-only verification, duplicate-name grouping, and conservative classification.

Only deeply verified asset-empty repositories become `DELETE_CANDIDATE`. Forks, duplicate names, and inactivity remain `MANUAL_REVIEW`. No GitHub mutation capability exists.

```bash
python -m pip install -e .
python -m compileall -q src scripts tests
python scripts/check_safety.py
python -m unittest discover -s tests -v
```
