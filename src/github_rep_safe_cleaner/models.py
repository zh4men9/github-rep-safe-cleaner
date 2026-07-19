from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

AssessmentCategory = Literal["DELETE_CANDIDATE", "MANUAL_REVIEW", "KEEP"]
Visibility = Literal["public", "private", "internal"]


@dataclass(slots=True)
class DeepEvidence:
    checked: bool = False
    has_commits: bool | None = None
    has_releases: bool | None = None
    has_issues: bool | None = None
    has_pull_requests: bool | None = None
    has_branches: bool | None = None
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RepositoryRecord:
    id: int
    name: str
    full_name: str
    html_url: str
    visibility: Visibility
    private: bool
    fork: bool
    archived: bool
    disabled: bool
    size_kb: int
    default_branch: str | None
    language: str | None
    description: str | None
    homepage: str | None
    created_at: str
    updated_at: str
    pushed_at: str | None
    stargazers_count: int
    watchers_count: int
    forks_count: int
    open_issues_count: int
    has_issues: bool
    has_projects: bool
    has_wiki: bool
    has_pages: bool
    has_discussions: bool
    is_template: bool
    topics: list[str] = field(default_factory=list)
    deep: DeepEvidence = field(default_factory=DeepEvidence)

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "RepositoryRecord":
        visibility = payload.get("visibility")
        if visibility not in {"public", "private", "internal"}:
            visibility = "private" if payload.get("private") else "public"
        return cls(
            id=int(payload["id"]),
            name=str(payload["name"]),
            full_name=str(payload["full_name"]),
            html_url=str(payload["html_url"]),
            visibility=visibility,
            private=bool(payload.get("private", False)),
            fork=bool(payload.get("fork", False)),
            archived=bool(payload.get("archived", False)),
            disabled=bool(payload.get("disabled", False)),
            size_kb=int(payload.get("size", 0)),
            default_branch=payload.get("default_branch"),
            language=payload.get("language"),
            description=payload.get("description"),
            homepage=payload.get("homepage"),
            created_at=str(payload.get("created_at", "")),
            updated_at=str(payload.get("updated_at", "")),
            pushed_at=payload.get("pushed_at"),
            stargazers_count=int(payload.get("stargazers_count", 0)),
            watchers_count=int(payload.get("watchers_count", 0)),
            forks_count=int(payload.get("forks_count", 0)),
            open_issues_count=int(payload.get("open_issues_count", 0)),
            has_issues=bool(payload.get("has_issues", False)),
            has_projects=bool(payload.get("has_projects", False)),
            has_wiki=bool(payload.get("has_wiki", False)),
            has_pages=bool(payload.get("has_pages", False)),
            has_discussions=bool(payload.get("has_discussions", False)),
            is_template=bool(payload.get("is_template", False)),
            topics=list(payload.get("topics") or []),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Assessment:
    repository: RepositoryRecord
    category: AssessmentCategory
    confidence: float
    priority: int
    reasons: list[str]
    counter_evidence: list[str]
    duplicate_group: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository.to_dict(),
            "category": self.category,
            "confidence": round(self.confidence, 3),
            "priority": self.priority,
            "reasons": self.reasons,
            "counter_evidence": self.counter_evidence,
            "duplicate_group": self.duplicate_group,
        }
