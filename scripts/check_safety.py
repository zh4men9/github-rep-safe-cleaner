from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXECUTABLE_ROOTS = [ROOT / "src", ROOT / "scripts", ROOT / ".github"]
FORBIDDEN_TEXT = [
    "gh repo " + "delete",
    "delete_repo",
    "repos." + "delete",
    "method=\"" + "DELETE" + "\"",
    "method='" + "DELETE" + "'",
]


def iter_files():
    for base in EXECUTABLE_ROOTS:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".yml", ".yaml"}:
                yield path


def check_text() -> list[str]:
    errors: list[str] = []
    for path in iter_files():
        text = path.read_text(encoding="utf-8")
        if path.resolve() == Path(__file__).resolve():
            continue
        for token in FORBIDDEN_TEXT:
            if token in text:
                errors.append(f"{path.relative_to(ROOT)} contains forbidden operation token: {token}")
    return errors


def check_python_ast() -> list[str]:
    errors: list[str] = []
    for path in iter_files():
        if path.suffix != ".py" or path.resolve() == Path(__file__).resolve():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in {"post", "put", "patch", "delete"}:
                    errors.append(f"{path.relative_to(ROOT)}:{node.lineno} calls .{node.func.attr}()")
    return errors


def check_workflow_permissions() -> list[str]:
    errors: list[str] = []
    workflow = ROOT / ".github" / "workflows" / "ci.yml"
    if not workflow.exists():
        return ["Missing .github/workflows/ci.yml"]
    text = workflow.read_text(encoding="utf-8")
    if not re.search(r"(?m)^permissions:\s*\n\s+contents:\s+read\s*$", text):
        errors.append("CI workflow must declare only contents: read at top level")
    return errors


def main() -> int:
    errors = check_text() + check_python_ast() + check_workflow_permissions()
    if errors:
        print("SAFETY CHECK FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Safety check passed: executable paths contain no repository mutation route.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
