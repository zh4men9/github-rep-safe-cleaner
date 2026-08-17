# Validation

## Verified offline / CI before v1.1

- Python source compiles.
- GET/HEAD-only client rejects mutation methods.
- Endpoint allowlist rejects unknown paths.
- Classification tests cover verified-empty, duplicate, fork, private keep, and public keep cases.
- Report generation writes JSON, CSV, Markdown, HTML, and manifest artifacts.
- Review page contains no browser `fetch` call.
- Safety scanner checks executable paths and CI permission scope.
- Demo run generates non-empty artifacts.

## First real-account evidence — 2026-08-17

- Editable install: PASS.
- Safety gate: PASS.
- Original 7 unit tests: PASS.
- Demo generation: PASS.
- Authentication: PASS as `zh4men9`.
- Owned repository inventory: PASS, 228 repositories.
- Deep-verification target selection: PASS, 94 targets.
- Full deep scan: FAIL in v1.0 because uncaught connection resets terminated the process at 13/94 and 2/94 on two runs.

## v1.1 regression evidence

- Transient connection reset followed by success is covered by a retry regression test.
- Exhausted network retries become `GitHubApiError` rather than escaping the transport boundary.
- A repository-level exhausted transport failure records unknown evidence and skips redundant remaining probes.
- Successful checkpoint entries resume only when repository ID and update fingerprints match.
- Failed checkpoint evidence and changed repository fingerprints are re-probed.

## Still required

- Latest v1.1 GitHub Actions head must pass after release metadata is committed.
- Real scan of the user's 228 repositories must reach report generation or degrade per-repository failures to `MANUAL_REVIEW` without aborting.
- Browser review and decisions export must be checked on the user's Mac.
