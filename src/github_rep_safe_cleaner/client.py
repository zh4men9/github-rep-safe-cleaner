from __future__ import annotations

import json
import os
import random
import re
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from http.client import HTTPException
from typing import Any, Iterator
from urllib.error import HTTPError, URLError
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
_RETRYABLE_HTTP_STATUS = {429, 500, 502, 503, 504}


@dataclass(slots=True)
class ApiResponse:
    data: Any
    headers: dict[str, str]
    status: int


class ReadOnlyGitHubClient:
    """A deliberately narrow GitHub REST client that permits GET/HEAD only."""

    def __init__(
        self,
        token: str,
        base_url: str = "https://api.github.com",
        timeout: int = 30,
        *,
        max_retries: int = 5,
        backoff_base: float = 0.75,
        max_backoff: float = 8.0,
        sleeper: Callable[[float], None] | None = None,
        jitter: Callable[[], float] | None = None,
        on_retry: Callable[[str], None] | None = None,
    ):
        if not token.strip():
            raise ValueError("A GitHub token is required to inspect private repositories.")
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if backoff_base < 0 or max_backoff < 0:
            raise ValueError("retry backoff values must be >= 0")
        self._token = token.strip()
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._max_backoff = max_backoff
        self._sleep = sleeper or time.sleep
        self._jitter = jitter or random.random
        self._on_retry = on_retry or (lambda _: None)
        self.last_rate_limit: dict[str, str] = {}
        self.retry_events = 0

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

        for attempt in range(self._max_retries + 1):
            request = Request(
                url,
                method=method.upper(),
                headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {self._token}",
                    "X-GitHub-Api-Version": "2022-11-28",
                    "User-Agent": "github-rep-safe-cleaner/1.1",
                },
            )
            try:
                with urlopen(request, timeout=self._timeout) as response:
                    raw = response.read()
                    data = json.loads(raw.decode("utf-8")) if raw else None
                    headers = _normalize_headers(response.headers)
                    self._update_rate_limit(headers)
                    return ApiResponse(data=data, headers=headers, status=response.status)
            except HTTPError as exc:
                headers = _normalize_headers(exc.headers)
                self._update_rate_limit(headers)
                try:
                    body = exc.read().decode("utf-8", errors="replace")
                except Exception:
                    body = ""
                message = f"GitHub API {exc.code} for {path}: {body[:500]}"
                if self._is_retryable_http(exc.code, headers) and attempt < self._max_retries:
                    self._wait_before_retry(attempt, path, message, headers)
                    continue
                raise GitHubApiError(message) from exc
            except json.JSONDecodeError as exc:
                message = f"GitHub returned invalid JSON for {path}: {exc}"
                if attempt < self._max_retries:
                    self._wait_before_retry(attempt, path, message, {})
                    continue
                raise GitHubApiError(message) from exc
            except (URLError, HTTPException, OSError) as exc:
                message = f"{type(exc).__name__}: {exc}"
                if attempt < self._max_retries:
                    self._wait_before_retry(attempt, path, message, {})
                    continue
                raise GitHubApiError(
                    f"GitHub network error after {attempt + 1} attempts for {path}: {message}"
                ) from exc

        raise AssertionError("unreachable retry state")

    def _wait_before_retry(self, attempt: int, path: str, reason: str, headers: dict[str, str]) -> None:
        delay = self._retry_delay(attempt, headers)
        retry_number = attempt + 1
        self.retry_events += 1
        self._on_retry(
            f"Retry {retry_number}/{self._max_retries} for {path} after {reason}; sleeping {delay:.2f}s"
        )
        self._sleep(delay)

    def _retry_delay(self, attempt: int, headers: dict[str, str]) -> float:
        retry_after = headers.get("retry-after")
        if retry_after:
            try:
                return min(60.0, max(0.0, float(retry_after)))
            except ValueError:
                pass
        jitter = min(1.0, max(0.0, float(self._jitter())))
        base = min(self._max_backoff, self._backoff_base * (2**attempt))
        return base * (0.75 + 0.5 * jitter)

    @staticmethod
    def _is_retryable_http(status: int, headers: dict[str, str]) -> bool:
        return status in _RETRYABLE_HTTP_STATUS or (status == 403 and "retry-after" in headers)

    def _update_rate_limit(self, headers: dict[str, str]) -> None:
        self.last_rate_limit = {
            key: headers[key]
            for key in ("x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset")
            if key in headers
        }

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
                if key in {"has_commits", "has_branches"} and (
                    "GitHub API 409" in message or "Git Repository is empty" in message
                ):
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


def _normalize_headers(headers: Any) -> dict[str, str]:
    if headers is None:
        return {}
    try:
        return {str(key).lower(): str(value) for key, value in headers.items()}
    except AttributeError:
        return {}


def _split_full_name(full_name: str) -> tuple[str, str]:
    parts = full_name.split("/", 1)
    if len(parts) != 2 or not all(parts):
        raise ValueError(f"Invalid repository full name: {full_name}")
    return parts[0], parts[1]
