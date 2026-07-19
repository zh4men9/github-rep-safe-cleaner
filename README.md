# github-rep-safe-cleaner

Version 0.1 establishes the non-negotiable safety boundary for a GitHub repository auditor.

- inspected repositories are read-only;
- the transport accepts GET/HEAD only;
- endpoints are allowlisted;
- CI has contents: read permission only;
- repository deletion, archiving, visibility changes, and settings mutation are absent and forbidden.

Run:

```bash
python -m pip install -e .
python -m compileall -q src scripts tests
python scripts/check_safety.py
python -m unittest discover -s tests -v
```
