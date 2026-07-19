from __future__ import annotations

from collections.abc import Callable

from .classify import build_duplicate_groups, needs_deep_probe
from .client import ReadOnlyGitHubClient
from .models import DeepEvidence, RepositoryRecord

ProgressCallback = Callable[[str], None]


def scan_account(
    client: ReadOnlyGitHubClient,
    *,
    deep_candidates: bool = True,
    progress: ProgressCallback | None = None,
) -> tuple[str, list[RepositoryRecord]]:
    emit = progress or (lambda _: None)
    login = client.authenticated_login()
    emit(f"Authenticated as {login}")
    payloads = client.list_owned_repositories()
    repositories = [RepositoryRecord.from_api(payload) for payload in payloads]
    emit(f"Loaded {len(repositories)} owned repositories")

    if deep_candidates:
        duplicates = build_duplicate_groups(repositories)
        targets = [repo for repo in repositories if needs_deep_probe(repo, duplicates)]
        emit(f"Deep read-only verification targets: {len(targets)}")
        for index, repo in enumerate(targets, start=1):
            emit(f"[{index}/{len(targets)}] Verify {repo.full_name}")
            evidence = client.probe_repository(repo.full_name)
            repo.deep = DeepEvidence(**evidence)
    return login, repositories
