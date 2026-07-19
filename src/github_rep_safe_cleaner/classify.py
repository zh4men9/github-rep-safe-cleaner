from __future__ import annotations

import re
from collections import defaultdict
from datetime import UTC, datetime
from typing import Iterable

from .models import Assessment, RepositoryRecord

_COPY_SUFFIX = re.compile(r"(?:[-_. ](?:copy|backup|bak|old|test|tmp|temp|demo|archive|v\d+|\d+))+$", re.IGNORECASE)


def normalize_name(name: str) -> str:
    lowered = name.strip().lower()
    previous = None
    while previous != lowered:
        previous = lowered
        lowered = _COPY_SUFFIX.sub("", lowered)
    return re.sub(r"[^a-z0-9]+", "", lowered)


def build_duplicate_groups(repositories: Iterable[RepositoryRecord]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for repo in repositories:
        key = normalize_name(repo.name)
        if key:
            groups[key].append(repo.full_name)
    return {key: values for key, values in groups.items() if len(values) > 1}


def needs_deep_probe(repo: RepositoryRecord, duplicate_groups: dict[str, list[str]]) -> bool:
    duplicate = normalize_name(repo.name) in duplicate_groups
    likely_empty = repo.size_kb == 0
    low_signal_fork = repo.fork and repo.stargazers_count == 0 and repo.forks_count == 0
    return likely_empty or duplicate or low_signal_fork


def assess_all(repositories: list[RepositoryRecord], now: datetime | None = None) -> list[Assessment]:
    now = now or datetime.now(UTC)
    duplicates = build_duplicate_groups(repositories)
    results = [assess_repository(repo, duplicates, now=now) for repo in repositories]
    category_order = {"DELETE_CANDIDATE": 0, "MANUAL_REVIEW": 1, "KEEP": 2}
    return sorted(
        results,
        key=lambda item: (
            category_order[item.category],
            item.priority,
            0 if item.repository.visibility == "public" else 1,
            item.repository.full_name.lower(),
        ),
    )


def assess_repository(
    repo: RepositoryRecord,
    duplicate_groups: dict[str, list[str]],
    *,
    now: datetime,
) -> Assessment:
    reasons: list[str] = []
    counter: list[str] = []
    key = normalize_name(repo.name)
    duplicate_group = key if key in duplicate_groups else None
    inactive_days = _inactive_days(repo, now)

    verified_empty = (
        repo.deep.checked
        and repo.deep.has_commits is False
        and repo.deep.has_releases is False
        and repo.deep.has_issues is False
        and repo.deep.has_pull_requests is False
        and repo.deep.has_branches is False
        and not repo.deep.errors
    )
    if verified_empty:
        reasons.append("深度只读复核确认：无提交、分支、Release、Issue 和 Pull Request")
        if repo.size_kb == 0:
            reasons.append("GitHub 元数据中的仓库大小为 0 KB")
        return Assessment(repo, "DELETE_CANDIDATE", 0.99, 10, reasons, counter, duplicate_group)

    if repo.stargazers_count:
        counter.append(f"有 {repo.stargazers_count} 个 star")
    if repo.forks_count:
        counter.append(f"有 {repo.forks_count} 个 fork")
    if repo.has_pages:
        counter.append("启用了 GitHub Pages")
    if repo.is_template:
        counter.append("被标记为模板仓库")
    if repo.has_discussions:
        counter.append("启用了 Discussions")
    if repo.description:
        counter.append("具有仓库说明")
    if repo.topics:
        counter.append("具有 topics 元数据")
    if repo.deep.has_releases:
        counter.append("存在 Release")
    if repo.deep.has_issues:
        counter.append("存在历史 Issue")
    if repo.deep.has_pull_requests:
        counter.append("存在历史 Pull Request")
    if repo.deep.has_commits:
        counter.append("存在提交历史")

    if repo.deep.errors:
        reasons.append("深度复核存在 API 读取错误，不能自动形成删除候选")
        counter.extend(repo.deep.errors)
        return Assessment(repo, "MANUAL_REVIEW", 0.95, 20, reasons, counter, duplicate_group)

    if repo.size_kb == 0 and not repo.deep.checked:
        reasons.append("仓库大小为 0 KB，但尚未完成深度只读复核")
        return Assessment(repo, "MANUAL_REVIEW", 0.9, 15, reasons, counter, duplicate_group)

    if duplicate_group:
        peers = [name for name in duplicate_groups[duplicate_group] if name != repo.full_name]
        reasons.append("名称疑似属于重复或历史副本组")
        reasons.append("同组仓库：" + ", ".join(peers))
        return Assessment(repo, "MANUAL_REVIEW", 0.86, 25, reasons, counter, duplicate_group)

    if repo.fork and repo.stargazers_count == 0 and repo.forks_count == 0:
        reasons.append("这是 fork，且当前没有 star 或下游 fork")
        reasons.append("系统未证明其没有独有提交，因此只进入人工复核")
        return Assessment(repo, "MANUAL_REVIEW", 0.82, 30, reasons, counter, duplicate_group)

    if repo.archived:
        reasons.append("仓库已归档但仍占据仓库列表，需要人工判断是否继续保留")
        return Assessment(repo, "MANUAL_REVIEW", 0.78, 35, reasons, counter, duplicate_group)

    if inactive_days is not None and inactive_days >= 1095:
        reasons.append(f"已约 {inactive_days} 天没有 push；不活跃本身不足以建议删除")
        return Assessment(repo, "MANUAL_REVIEW", 0.72, 40, reasons, counter, duplicate_group)

    if repo.visibility == "public" and not repo.description and not repo.topics:
        reasons.append("公开仓库缺少 description 和 topics，可能削弱公开主页的信息密度")
        return Assessment(repo, "MANUAL_REVIEW", 0.68, 45, reasons, counter, duplicate_group)

    reasons.append("没有发现足以进入删除候选的证据")
    return Assessment(repo, "KEEP", 0.8, 90, reasons, counter, duplicate_group)


def _inactive_days(repo: RepositoryRecord, now: datetime) -> int | None:
    value = repo.pushed_at or repo.updated_at or repo.created_at
    if not value:
        return None
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return max(0, (now - timestamp.astimezone(UTC)).days)
