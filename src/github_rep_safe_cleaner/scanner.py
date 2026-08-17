from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .classify import build_duplicate_groups, needs_deep_probe
from .client import ReadOnlyGitHubClient
from .models import DeepEvidence, RepositoryRecord

ProgressCallback = Callable[[str], None]


def scan_account(
    client: ReadOnlyGitHubClient,
    *,
    deep_candidates: bool = True,
    progress: ProgressCallback | None = None,
    checkpoint_path: Path | None = None,
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
        checkpoint = _load_checkpoint(checkpoint_path, login, emit)
        emit(f"Deep read-only verification targets: {len(targets)}")
        resumed = 0
        for index, repo in enumerate(targets, start=1):
            cached = _resumable_evidence(checkpoint.get(repo.full_name), repo)
            if cached is not None:
                repo.deep = cached
                resumed += 1
                emit(f"[{index}/{len(targets)}] Resume {repo.full_name}")
                continue

            emit(f"[{index}/{len(targets)}] Verify {repo.full_name}")
            evidence = client.probe_repository(repo.full_name)
            repo.deep = DeepEvidence(**evidence)
            checkpoint[repo.full_name] = {
                "repository_id": repo.id,
                "updated_at": repo.updated_at,
                "pushed_at": repo.pushed_at,
                "evidence": evidence,
            }
            _write_checkpoint(checkpoint_path, login, checkpoint)

        if resumed:
            emit(f"Resumed {resumed} successful deep verification result(s) from checkpoint")
    return login, repositories


def _load_checkpoint(
    checkpoint_path: Path | None,
    owner: str,
    emit: ProgressCallback,
) -> dict[str, dict[str, Any]]:
    if checkpoint_path is None or not checkpoint_path.exists():
        return {}
    try:
        payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        emit(f"Checkpoint ignored because it cannot be read: {exc}")
        return {}
    if payload.get("owner") != owner:
        emit("Checkpoint ignored because the authenticated owner changed")
        return {}
    repositories = payload.get("repositories")
    if not isinstance(repositories, dict):
        emit("Checkpoint ignored because its repositories field is invalid")
        return {}
    return {str(key): value for key, value in repositories.items() if isinstance(value, dict)}


def _resumable_evidence(entry: dict[str, Any] | None, repo: RepositoryRecord) -> DeepEvidence | None:
    if not entry:
        return None
    if entry.get("repository_id") != repo.id:
        return None
    if entry.get("updated_at") != repo.updated_at or entry.get("pushed_at") != repo.pushed_at:
        return None
    evidence = entry.get("evidence")
    if not isinstance(evidence, dict):
        return None
    if evidence.get("checked") is not True or evidence.get("errors"):
        return None
    try:
        return DeepEvidence(**evidence)
    except TypeError:
        return None


def _write_checkpoint(
    checkpoint_path: Path | None,
    owner: str,
    repositories: dict[str, dict[str, Any]],
) -> None:
    if checkpoint_path is None:
        return
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "owner": owner,
        "updated_at": datetime.now(UTC).isoformat(),
        "repositories": repositories,
    }
    temporary = checkpoint_path.with_name(checkpoint_path.name + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(checkpoint_path)
