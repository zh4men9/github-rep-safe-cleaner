# Risk register

| Risk | Control | Verification |
|---|---|---|
| Accidental repository mutation | GET/HEAD-only client and endpoint allowlist | client tests and safety gate |
| False deletion candidate | deep-empty requirement and explicit counter-evidence | classification tests and user review |
| Private data leakage | local artifacts ignored; no secrets in repository | review diff and `.gitignore` |
| API incompleteness | errors force manual review | real-account acceptance |
| Browser-side mutation | self-contained page with no network request | report test and JavaScript inspection |
