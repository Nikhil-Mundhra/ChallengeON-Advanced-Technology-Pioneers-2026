from __future__ import annotations

import ast
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .storage import atomic_write_json, read_json


SOURCE_ROOTS = ("src", "scripts", "tests")
DATA_SUFFIXES = {".parquet", ".csv", ".tsv", ".xlsx", ".xls", ".json", ".pkl"}


def _source_entry(root: Path, path: Path) -> dict[str, Any]:
    relative = str(path.relative_to(root))
    text = path.read_text(encoding="utf-8", errors="replace")
    symbols: list[dict[str, Any]] = []
    imports: list[str] = []
    try:
        tree = ast.parse(text)
        for node in tree.body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                symbols.append(
                    {"name": node.name, "kind": type(node).__name__, "line": node.lineno}
                )
            elif isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
    except SyntaxError:
        pass
    return {
        "path": relative,
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
        "lines": text.count("\n") + 1,
        "symbols": symbols,
        "imports": sorted(set(imports)),
    }


def _inventory(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    sources: list[dict[str, Any]] = []
    for directory in SOURCE_ROOTS:
        base = root / directory
        if base.exists():
            sources.extend(_source_entry(root, path) for path in sorted(base.rglob("*.py")))
    assets: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in DATA_SUFFIXES:
            continue
        relative = path.relative_to(root)
        if {".git", ".venv", "audit"} & set(relative.parts):
            continue
        stat = path.stat()
        assets.append(
            {
                "path": str(relative),
                "suffix": path.suffix.lower(),
                "size_bytes": stat.st_size,
                "modified_ns": stat.st_mtime_ns,
            }
        )
    digest = hashlib.sha256()
    for entry in sources:
        digest.update(f"{entry['path']}:{entry['sha256']}\n".encode())
    for entry in assets:
        digest.update(
            f"{entry['path']}:{entry['size_bytes']}:{entry['modified_ns']}\n".encode()
        )
    return sources, assets, digest.hexdigest()


def ensure_repository_map(root: Path, audit_dir: Path) -> dict[str, Any]:
    sources, assets, fingerprint = _inventory(root)
    discovery_dir = audit_dir / "discovery"
    current_path = discovery_dir / "repository_map.json"
    current = read_json(current_path, default={})
    if current.get("fingerprint") == fingerprint:
        return current
    result = {
        "schema_version": 1,
        "fingerprint": fingerprint,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "contract": (
            "Navigation metadata only. Finders must reproduce material claims with "
            "read-only tools before using them as audit evidence."
        ),
        "source_files": sources,
        "data_assets": assets,
    }
    discovery_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(discovery_dir / f"repository_map.{fingerprint[:12]}.json", result)
    atomic_write_json(current_path, result)
    return result


def context_for_task(repository_map: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    scope = task.get("scope", {})
    requested = {str(value) for value in scope.get("files", [])}
    terms = {
        Path(value).stem.lower()
        for value in requested
        if value and value != "DISCOVER"
    }
    selected = []
    related = []
    for entry in repository_map.get("source_files", []):
        path = entry["path"]
        if path in requested:
            selected.append(entry)
        elif path.startswith("tests/") and any(term in path.lower() for term in terms):
            related.append(entry)
        elif any(
            term in imported.lower()
            for term in terms
            for imported in entry.get("imports", [])
        ):
            related.append(entry)
    table_terms = {
        str(value).lower().replace(" ", "_")
        for value in scope.get("tables_or_sheets", [])
        if value not in {"NOT_APPLICABLE", "DISCOVER"}
    }
    assets = [
        entry
        for entry in repository_map.get("data_assets", [])
        if any(term in entry["path"].lower() for term in table_terms)
    ]
    return {
        "repository_fingerprint": repository_map.get("fingerprint"),
        "contract": repository_map.get("contract"),
        "scoped_source_files": selected,
        "related_source_files": related[:12],
        "matching_data_assets": assets[:20],
    }
