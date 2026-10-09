"""Package layering and code rules."""

from __future__ import annotations

from pathlib import Path
from tourism_twin.config import SETTINGS


def test_model_packages_have_no_row_loops():
    root = Path(SETTINGS.root) / "src" / "tourism_twin"
    offenders = [str(p.relative_to(root)) for package in ("models", "nowcast", "planning")
                 for p in (root / package).rglob("*.py") if ".iterrows(" in p.read_text()]
    assert offenders == []


# Allowed tourism_twin imports per package; nowcast and planning never import each other.
_BELOW_ADAPTERS = {"config", "domain", "features", "data", "models", "nowcast", "planning"}


ALLOWED_IMPORTS = {
    "domain": {"domain"},
    "features": {"domain", "features"},
    "data": {"config", "domain", "features", "data"},
    "models": {"config", "domain", "features", "models"},
    "nowcast": {"config", "domain", "features", "data", "models", "nowcast"},
    "planning": {"config", "domain", "features", "data", "models", "planning"},
    "reporting": _BELOW_ADAPTERS | {"reporting"},
    "cli": _BELOW_ADAPTERS | {"reporting", "cli"},
}


def _imported_packages(path: Path, package: str):
    """tourism_twin sub-packages a module imports, in any import form (absolute, aliased, relative)."""
    import ast

    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                if parts[0] == "tourism_twin" and len(parts) > 1:
                    yield parts[1]
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative: resolve against this module's package
                base = list(path.relative_to(Path(SETTINGS.root) / "src" / "tourism_twin").parts[:-1])
                base = base[:len(base) - (node.level - 1)] if node.level > 1 else base
                parts = base + (node.module.split(".") if node.module else [])
                yield parts[0] if parts else package
            elif node.module == "tourism_twin":
                yield from (alias.name for alias in node.names)
            elif node.module and node.module.startswith("tourism_twin."):
                yield node.module.split(".")[1]


def test_packages_import_only_lower_layers():
    root = Path(SETTINGS.root) / "src" / "tourism_twin"
    violations = [f"{path.relative_to(root)} imports {target}"
                  for package, allowed in ALLOWED_IMPORTS.items()
                  for path in (root / package).rglob("*.py")
                  for target in _imported_packages(path, package) if target not in allowed]
    assert violations == []
