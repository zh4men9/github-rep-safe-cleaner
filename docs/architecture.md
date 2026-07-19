# Architecture

```text
GitHub REST API (GET only)
        |
        v
ReadOnlyGitHubClient
        |
        v
RepositoryRecord + candidate-targeted deep evidence
        |
        v
Conservative classification
        |
        v
Immutable JSON / CSV / Markdown / HTML run artifacts
        |
        v
User reviews every candidate and performs any real GitHub action manually
```

The runtime is Python 3.11 standard library only. The browser review page is self-contained and performs no network request. Inspected repositories never enter a write path because no write path exists.
