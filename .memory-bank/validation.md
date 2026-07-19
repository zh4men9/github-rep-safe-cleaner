# Validation

## Verified offline

- Python source compiles.
- GET/HEAD-only client rejects mutation methods.
- Endpoint allowlist rejects unknown paths.
- Classification tests cover verified-empty, duplicate, fork, private keep, and public keep cases.
- Report generation writes JSON, CSV, Markdown, HTML, and manifest artifacts.
- Review page contains no browser `fetch` call.
- Safety scanner checks executable paths and CI permission scope.
- Demo run generates non-empty artifacts.

## Not yet verified

- Real GitHub authentication on the user's Mac.
- Complete scan of all owned public/private repositories.
- GitHub rate-limit behavior for the user's repository count.
- Candidate quality on real repositories.
- Browser review and decisions export on the user's Mac.
