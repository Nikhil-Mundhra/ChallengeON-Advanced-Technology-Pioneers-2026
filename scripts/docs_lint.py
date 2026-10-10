#!/usr/bin/env python3
"""Checks the guide and docs graph: every .md reachable from AGENTS.md, an index.md with a sorted map in
every docs folder, CLAUDE.md equal to AGENTS.md, no docs -> agents links, result numbers only in
docs/results and docs/evidence, kebab-case doc names, existing referenced paths.

Report-only by default (exit 0); --strict exits 1 on any finding."""

from __future__ import annotations

import argparse
import glob
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRY = "AGENTS.md"
ENTRY_COPY = "CLAUDE.md"
EXCLUDED = (".claude/", ".venv/", ".git/", "node_modules/", "web/public/data/", "web/dist/", "lake/", "output/",
            "meta/research/", "meta/audits/")
NUMBERS_ALLOWED = ("docs/results/", "docs/evidence/", "meta/")
# Root standards: their role is conventional, so no route has to reach them.
UNROUTED = {ENTRY_COPY}
# A backticked token is checked for existence only when it starts at one of these root entries.
PATH_ROOTS = {"agents", "docs", "src", "web", "tests", "scripts", "meta", ".agents", ".opencode",
              "AGENTS.md", "CLAUDE.md", "README.md", "Makefile", "pyproject.toml"}
GENERATED = ("web/public/data", "web/dist", "web/node_modules", "output", "audit", ".run")

RESULT_NUMBER = re.compile(r"\d+\.\d\d%")
MAP_LINE = re.compile(r"^(\S+) : \S")
BACKTICK = re.compile(r"`([^`\n]+)`")
LINK = re.compile(r"\]\(([^)\s]+)\)")
DOCS_TO_AGENTS = re.compile(r"(^|[^A-Za-z0-9_.-])agents/")
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*\.md$")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def markdown_files() -> list[str]:
    files = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.md"],
                           cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    return sorted({on_disk(f) for f in files if (ROOT / f).exists() and not f.startswith(EXCLUDED)})


def on_disk(path: str) -> str:
    """The path as spelled on disk; the index keeps the old spelling of a case-only rename on a
    case-insensitive filesystem."""
    parts, folder = [], ROOT
    for part in path.split("/"):
        names = {name.lower(): name for name in (p.name for p in folder.iterdir())}
        part = part if (folder / part).exists() and part in names.values() else names.get(part.lower(), part)
        parts.append(part)
        folder = folder / part
    return "/".join(parts)


def sections(text: str) -> dict[str, str]:
    """`## ` heading -> body; text before the first heading is under ''."""
    result: dict[str, list[str]] = {"": []}
    current, fenced = "", False
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        if not fenced and line.startswith("## "):
            current = line[3:].strip()
            result[current] = []
        else:
            result[current].append(line)
    return {k: "\n".join(v) for k, v in result.items()}


def fenced_lines(text: str) -> list[str]:
    """Lines inside non-Mermaid code fences."""
    lines, fence = [], None
    for line in text.splitlines():
        if line.startswith("```"):
            fence = line[3:].strip() if fence is None else None
            continue
        if fence is not None and fence != "mermaid":
            lines.append(line)
    return lines


def map_paths(text: str) -> list[str]:
    return [m.group(1) for m in map(MAP_LINE.match, fenced_lines(text)) if m]


def links(text: str, source: str) -> list[str]:
    out = []
    for target in LINK.findall(text):
        if re.match(r"^[a-z]+:", target) or target.startswith("#"):
            continue
        resolved = (ROOT / source).parent / target.split("#")[0]
        out.append(resolved.resolve().relative_to(ROOT).as_posix() if resolved.resolve().is_relative_to(ROOT)
                   else target)
    return out


def expand(token: str) -> list[str]:
    """A route token with a <placeholder> names every matching path."""
    if "<" not in token:
        return [token]
    pattern = re.sub(r"<[^>]+>", "*", token)
    return sorted(rel(Path(p)) for p in glob.glob(str(ROOT / pattern)))


def edges(path: str) -> list[str]:
    text = (ROOT / path).read_text(encoding="utf-8")
    if path.startswith("docs/"):
        return map_paths(text) + links(text, path) if path.endswith("/index.md") or path == "docs/index.md" else []
    is_guide = path == ENTRY or path.startswith("agents/")
    if is_guide:
        parts = sections(text)
        tokens = BACKTICK.findall("\n".join(parts.get(k, "") for k in ("Route", "Calls")))
        tokens += map_paths(parts.get("File structure", ""))
        return [p for t in tokens for p in expand(t) if p.endswith(".md")]
    return links(text, path)


def reachable() -> set[str]:
    seen: set[str] = set()
    queue = [ENTRY]
    while queue:
        path = queue.pop(0)
        if path in seen or not (ROOT / path).is_file():
            continue
        seen.add(path)
        queue.extend(p for p in edges(path) if p.endswith(".md"))
    return seen


def as_repo_path(token: str) -> str | None:
    path = re.sub(r"[:#].*$", "", token).rstrip("/")
    if not path or re.search(r"[<>*{}$|\s]", path):
        return None
    if path.split("/")[0] not in PATH_ROOTS or path.startswith(GENERATED):
        return None
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--strict", action="store_true", help="exit 1 on any finding")
    args = parser.parse_args()

    findings: list[str] = []
    files = markdown_files()

    reached = reachable()
    for path in files:
        if path not in reached and path not in UNROUTED:
            findings.append(f"[unreachable] {path}: no Route, Calls, map or link edge from {ENTRY}")

    for folder in sorted({p.parent for p in (ROOT / "docs").rglob("*") if p.is_file()} | {ROOT / "docs"}):
        index = folder / "index.md"
        if not index.exists():
            findings.append(f"[no index] {rel(folder)}: missing index.md")
            continue
        paths = map_paths(index.read_text(encoding="utf-8"))
        if not paths:
            findings.append(f"[no map] {rel(index)}: no `path : responsibility` map")
        for before, after in zip(paths, paths[1:]):
            if before > after:
                findings.append(f"[unsorted map] {rel(index)}: {after} after {before}")

    entry, copy = ROOT / ENTRY, ROOT / ENTRY_COPY
    if not copy.exists() or copy.read_bytes() != entry.read_bytes():
        findings.append(f"[entry copy] {ENTRY_COPY}: differs from {ENTRY}; cp {ENTRY} {ENTRY_COPY}")

    for path in files:
        text = (ROOT / path).read_text(encoding="utf-8")
        lines = text.splitlines()
        if path.startswith("docs/"):
            for i, line in enumerate(lines, 1):
                if DOCS_TO_AGENTS.search(line):
                    findings.append(f"[docs->agents] {path}:{i}: {line.strip()[:100]}")
            if not KEBAB.match(Path(path).name):
                findings.append(f"[name] {path}: not kebab-case")
        if not path.startswith(NUMBERS_ALLOWED) and not path.startswith(".agents/"):
            for i, line in enumerate(lines, 1):
                for number in RESULT_NUMBER.findall(line):
                    findings.append(f"[result number] {path}:{i}: {number} outside docs/results and docs/evidence")
        if path.startswith(".agents/"):
            continue
        tokens = BACKTICK.findall(text) + map_paths(text)
        for token in tokens:
            repo_path = as_repo_path(token)
            if repo_path and not (ROOT / repo_path).exists():
                findings.append(f"[missing path] {path}: {repo_path}")
        for target in links(text, path):
            if not re.match(r"^[a-z]+:", target) and not (ROOT / target).exists():
                findings.append(f"[missing link] {path}: {target}")

    for finding in findings:
        print(finding)
    print(f"docs-lint: {len(findings)} finding(s) in {len(files)} files, {len(reached)} reachable"
          + ("" if args.strict else " (report-only)"))
    return 1 if findings and args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
