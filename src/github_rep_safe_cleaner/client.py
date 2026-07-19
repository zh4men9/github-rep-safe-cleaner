from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from typing import Any, Iterator
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class SafetyViolation(RuntimeError):
    """Raised when code attempts a non-read-only GitHub operation."""


class GitHubApiError(RuntimeError):
    pass


_ALLOWED_PATHS = (
    re.compile(r"^/user$"),
    re.compile(r"^/user/repos$"),
    re.compile(r"^/repos/[^/]+/[^/]+$"),
    re.compile(r"^/repos/[^/]+/[^/]+/(commits|releases|issues|pulls|branches)$"),
)


@dataclass(slots=True)
class ApiResponse:
    data: Any
    headers: dict[str, str]
    status: int


class ReadOnlyGitHubClient:
    """A deliberately narrow GitHub REST client that permits GET/HEAD only."""

    def __init__(self, token: str, base_url: str = "https://api.github.com", timeout: int = 30):
        if not token.strip():
            raise ValueError("A GitHub token is required to inspect private repositories.")
        self._token = token.strip()
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self.last_rate_limit: dict[str, str] = {}

    @staticmethod
    def _validate(method: str, path: str) -> None:
        normalized = method.upper()
        if normalized not in {"GET", "HEAD"}:
            raise SafetyViolation(f"Blocked non-read-only HTTP method: {normalized}")
        if not any(pattern.fullmatch(path) for pattern in _ALLOWED_PATHS):
            raise SafetyViolation(f"Blocked GitHub endpoint outside the read-only allowlist: {path}")

    def request(self, path: str, *, params: dict[str, Any] | None = None, method: str = "GET") -> ApiResponse:
        self._validate(method, path)
        query = urlencode({key: value for key, value in (params or {}).items() if value is not None})
        url = f"{self._base_url}{path}"
        if query:
            url = f"{url}?{query}"
        request = Request(
            url,
            method=method.upper(),
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self._token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "github-rep-safe-cleaner/1.0",
            },
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                raw = response.read()
                data = json.loads(raw.decode("utf-8")) if raw else None
                headers = {key.lower(): value for key, value in response.headers.items()}
                self.last_rate_limit = {
                    key: headers[key]
                    for key in ("x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset")
                    if key in headers
                }
                return ApiResponse(data=data, headers=headers, status=response.status)
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise GitHubApiError(f"GitHub API {exc.code} for {path}: {body[:500]}") from exc

    def iter_pages(self, path: str, *, params: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
        page = 1
        while True:
            page_params = {**(params or {}), "per_page": 100, "page": page}
            response = self.request(path, params=page_params)
            if not isinstance(response.data, list):
                raise GitHubApiError(f"Expected a list response for {path}")
            for item in response.data:
                if isinstance(item, dict):
                    yield item
            if len(response.data) < 100:
                break
            page += 1

    def authenticated_login(self) -> str:
        response = self.request("/user")
        if not isinstance(response.data, dict) or not response.data.get("login"):
            raise GitHubApiError("Unable to determine the authenticated GitHub login.")
        return str(response.data["login"])

    def list_owned_repositories(self) -> list[dict[str, Any]]:
        return list(
            self.iter_pages(
                "/user/repos",
                params={
                    "affiliation": "owner",
                    "visibility": "all",
                    "sort": "full_name",
                    "direction": "asc",
                },
            )
        )

    def probe_repository(self, full_name: str) -> dict[str, Any]:
        owner, name = _split_full_name(full_name)
        root = f"/repos/{owner}/{name}"
        result: dict[str, Any] = {"checked": True, "errors": []}
        probes = {
            "has_commits": (f"{root}/commits", {}),
            "has_releases": (f"{root}/releases", {}),
            "has_issues": (f"{root}/issues", {"state": "all"}),
            "has_pull_requests": (f"{root}/pulls", {"state": "all"}),
            "has_branches": (f"{root}/branches", {}),
        }
        for key, (path, params) in probes.items():
            try:
                response = self.request(path, params={**params, "per_page": 1, "page": 1})
                result[key] = bool(response.data)
            except GitHubApiError as exc:
                message = str(exc)
                if key in {"has_commits", "has_branches"} and ("GitHub API 409" in message or "Git Repository is empty" in message):
                    result[key] = False
                else:
                    result[key] = None
                    result["errors"].append(f"{key}: {message}")
        return result


def resolve_token() -> str:
    for name in ("GH_TOKEN", "GITHUB_TOKEN"):
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    try:
        process = subprocess.run(
            ["gh", "auth", "token"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(
            "No GitHub token found. Set GH_TOKEN/GITHUB_TOKEN or authenticate GitHub CLI with `gh auth login`."
        ) from exc
    token = process.stdout.strip()
    if not token:
        raise RuntimeError("GitHub CLI returned an empty token.")
    return token


def _split_full_name(full_name: str) -> tuple[str, str]:
    parts = full_name.split("/", 1)
    if len(parts) != 2 or not all(parts):
        raise ValueError(f"Invalid repository full name: {full_name}")
    return parts[0], parts[1]
