from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .classify import assess_all
from .client import ReadOnlyGitHubClient, resolve_token
from .models import DeepEvidence, RepositoryRecord
from .report import default_run_directory, write_run
from .scanner import scan_account


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-safe-cleaner",
        description="Read-only GitHub repository inventory and manual cleanup candidate review.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Scan all public and private repositories owned by the authenticated account.")
    scan.add_argument("--output", type=Path, default=None, help="Run output directory.")
    scan.add_argument("--no-deep", action="store_true", help="Skip deep read-only verification of candidate repositories.")
    scan.add_argument("--base-url", default="https://api.github.com", help="GitHub REST API base URL.")
    scan.add_argument(
        "--max-retries",
        type=int,
        default=5,
        help="Maximum retries for transient read-only GitHub requests (default: 5).",
    )

    analyze = sub.add_parser("analyze", help="Analyze a saved GitHub API repository list without network access.")
    analyze.add_argument("input", type=Path, help="JSON list returned by the GitHub repositories API.")
    analyze.add_argument("--evidence", type=Path, help="Optional JSON mapping full_name to deep evidence.")
    analyze.add_argument("--output", type=Path, default=None, help="Run output directory.")
    analyze.add_argument("--owner", default="offline", help="Owner label for the report.")

    demo = sub.add_parser("demo", help="Generate a complete demo report from bundled test fixtures.")
    demo.add_argument("--output", type=Path, default=Path("artifacts/demo"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "scan":
            return _run_scan(args)
        if args.command == "analyze":
            return _run_analyze(args)
        if args.command == "demo":
            fixture = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "repos.json"
            evidence = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "evidence.json"
            return _analyze_files(fixture, evidence, args.output, "demo-user")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 2


def _run_scan(args: argparse.Namespace) -> int:
    output = args.output or default_run_directory()
    checkpoint = output / "checkpoint.json"
    client = ReadOnlyGitHubClient(
        resolve_token(),
        base_url=args.base_url,
        max_retries=args.max_retries,
        on_retry=lambda message: print(message, file=sys.stderr),
    )
    owner, repositories = scan_account(
        client,
        deep_candidates=not args.no_deep,
        progress=lambda message: print(message, file=sys.stderr),
        checkpoint_path=checkpoint,
    )
    assessments = assess_all(repositories)
    paths = write_run(output, owner=owner, assessments=assessments, rate_limit=client.last_rate_limit)
    if checkpoint.exists():
        paths["checkpoint"] = checkpoint
    print(f"retry_events: {client.retry_events}")
    _print_paths(paths)
    return 0


def _run_analyze(args: argparse.Namespace) -> int:
    return _analyze_files(args.input, args.evidence, args.output or default_run_directory(), args.owner)


def _analyze_files(input_path: Path, evidence_path: Path | None, output: Path, owner: str) -> int:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Input must be a JSON list of GitHub repository objects.")
    repositories = [RepositoryRecord.from_api(item) for item in payload]
    if evidence_path:
        evidence_payload = json.loads(evidence_path.read_text(encoding="utf-8"))
        for repo in repositories:
            value = evidence_payload.get(repo.full_name)
            if value:
                repo.deep = DeepEvidence(**value)
    assessments = assess_all(repositories)
    paths = write_run(output, owner=owner, assessments=assessments)
    _print_paths(paths)
    return 0


def _print_paths(paths: dict[str, Path]) -> None:
    for name, path in paths.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    raise SystemExit(main())
