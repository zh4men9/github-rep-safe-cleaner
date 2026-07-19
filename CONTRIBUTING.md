# Contributing

Before proposing changes:

1. Preserve the no-mutation boundary.
2. Run `python scripts/check_safety.py`.
3. Run `python -m unittest discover -s tests -v`.
4. Generate the offline demo.
5. Explain how the change reduces false positives or improves evidence quality.

Changes that add repository deletion, archiving, visibility changes, or inspected-repository writes are out of scope and must not be accepted.
