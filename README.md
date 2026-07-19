# github-rep-safe-cleaner

A deliberately read-only GitHub repository auditor for finding repositories that deserve manual cleanup review.

The project scans **both public and private repositories owned by the authenticated account**, gathers evidence, classifies repositories conservatively, and generates a local review page plus JSON/CSV/Markdown reports.

It does **not** delete repositories, archive repositories, change visibility, edit settings, or write to any inspected repository. Every real GitHub action remains manual.

## What it produces

Each run writes an immutable directory under `artifacts/runs/<timestamp>/`:

```text
inventory.json
inventory.csv
report.md
candidates.md
review.html
manifest.json
```

`review.html` is a fully local page. It makes no network requests. Decisions are stored in browser `localStorage` and can be exported as `decisions.json`.

## Classification

- `DELETE_CANDIDATE`: only when deep read-only verification confirms no commits, branches, releases, issues, or pull requests.
- `MANUAL_REVIEW`: duplicates, old forks, archived repositories, long-inactive repositories, incomplete evidence, and public repositories with weak metadata.
- `KEEP`: no deletion-grade evidence was found.

Inactivity alone never creates a deletion candidate. Fork status alone never creates a deletion candidate.

## Install

Python 3.11+ is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

The scanner needs authenticated GitHub read access to inspect private repositories. It resolves credentials in this order:

1. `GH_TOKEN`
2. `GITHUB_TOKEN`
3. `gh auth token`

Do not place tokens in this repository.

## Run a complete account scan

```bash
repo-safe-cleaner scan
```

The command uses only `GET` requests against a narrow endpoint allowlist. Candidate-like repositories receive deeper read-only checks.

To choose an output directory:

```bash
repo-safe-cleaner scan --output artifacts/runs/my-first-scan
```

To skip deep checks temporarily:

```bash
repo-safe-cleaner scan --no-deep
```

A no-deep run cannot promote a size-zero repository directly to `DELETE_CANDIDATE`; it remains `MANUAL_REVIEW`.

## Offline demo

```bash
repo-safe-cleaner demo --output artifacts/demo
open artifacts/demo/review.html
```

## Validate

```bash
python -m compileall -q src scripts tests
python scripts/check_safety.py
python -m unittest discover -s tests -v
repo-safe-cleaner demo --output artifacts/demo
```

## Safety model

The safety boundary is structural rather than procedural:

- the GitHub client rejects every method except `GET` and `HEAD`;
- only explicitly allowlisted read endpoints are accepted;
- the package contains no repository mutation command;
- CI has only `contents: read` permission;
- a static and AST-based safety gate scans executable paths;
- generated pages contain no GitHub API client;
- reports are advisory and require manual review.

See [`docs/safety-model.md`](docs/safety-model.md).

## Current status

Version `1.0.0` implements the full read-only pipeline. The remaining acceptance step is a real scan of the owner's GitHub account and manual inspection of the generated `review.html`.
