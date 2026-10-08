"""Feature registry: each derived column is declared once, with its kind and its inputs.

A spec's `requires` names input columns or other specs; "@param" names a column chosen per call
(e.g. "@anchor" is the date column a calendar feature reads). `apply` resolves the requested
features and everything they depend on in dependency order and computes each exactly once.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, Tuple, Union

import pandas as pd

Output = Union[pd.Series, pd.DataFrame]


class Kind(Enum):
    RATIO = "ratio"          # recomputed from summed parts at every grain; never summed or averaged
    FLAG = "flag"            # 0/1 quality or completeness marker
    CALENDAR = "calendar"    # derived from a date
    ATTRIBUTE = "attribute"  # derived from an entity key (e.g. market archetype)
    LAG = "lag"              # shifted values within an entity's series


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    kind: Kind
    requires: Tuple[str, ...]
    compute: Callable[..., Output] = field(repr=False)


class FeatureRegistry:
    def __init__(self) -> None:
        self._specs: Dict[str, FeatureSpec] = {}

    def feature(self, kind: Kind, requires: Iterable[str]) -> Callable[[Callable[..., Output]], Callable[..., Output]]:
        """Decorator: register `fn(frame, **params)` under its function name."""
        def register(fn: Callable[..., Output]) -> Callable[..., Output]:
            self.register(FeatureSpec(fn.__name__, kind, tuple(requires), fn))
            return fn
        return register

    def register(self, spec: FeatureSpec) -> None:
        if spec.name in self._specs:
            raise ValueError(f"Feature {spec.name!r} is already registered")
        self._specs[spec.name] = spec

    def spec(self, name: str) -> FeatureSpec:
        return self._specs[name]

    def resolve(self, targets: Iterable[str], available: Iterable[str], params: Dict[str, Any]) -> List[FeatureSpec]:
        """Specs needed for `targets`, dependencies first. Raises on a cycle or a missing input."""
        available = set(available)
        order: List[FeatureSpec] = []
        state: Dict[str, str] = {}

        def visit(name: str, path: Tuple[str, ...]) -> None:
            if state.get(name) == "done":
                return
            if state.get(name) == "visiting":
                raise ValueError(f"Feature dependency cycle: {' -> '.join(path + (name,))}")
            spec = self._specs.get(name)
            if spec is None:
                raise KeyError(f"Unknown feature {name!r}")
            state[name] = "visiting"
            for requirement in spec.requires:
                column = params[requirement[1:]] if requirement.startswith("@") else requirement
                if column in self._specs:
                    visit(column, path + (name,))
                elif column not in available:
                    raise KeyError(f"Feature {name!r} requires missing column {column!r}")
            state[name] = "done"
            order.append(spec)

        for target in targets:
            visit(target, ())
        return order

    def apply(self, frame: pd.DataFrame, targets: Iterable[str], **params: Any) -> pd.DataFrame:
        """Return `frame` with the requested features (and their dependencies) appended in order."""
        frame = frame.copy()
        for spec in self.resolve(targets, frame.columns, params):
            output = spec.compute(frame, **params)
            if isinstance(output, pd.DataFrame):
                frame = pd.concat([frame, output], axis=1)
            else:
                frame[spec.name] = output
        return frame


PANEL_FEATURES = FeatureRegistry()
