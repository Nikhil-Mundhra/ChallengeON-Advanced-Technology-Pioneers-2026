"""ModelSpec: a log-additive model declared as data.

    spec = ModelSpec(components=[("arrivals_kernel", {"max_lag": 21}), "annual_fourier", "weekday"],
                     fitter=("backfitting", {"max_iter": 200, "tol": 1e-6}),
                     rules=NOWCAST_ROWS, weighting=None)
    model = spec.build()              # a fresh, unfitted AdditiveLogModel on every call

A variant (ablation, another block pairing, another weighting) is another ModelSpec, made with
with_components / replace_component / with_weighting, never new code. Specs are immutable:
entries and options are frozen on construction (hashable, picklable), so one spec can be shared,
used as a cache key and built many times.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Iterator, List, Mapping, Optional, Sequence, Tuple

from tourism_twin.models.composite import AdditiveLogModel
from tourism_twin.models.handler import RowRule
from tourism_twin.models.registry import COMPONENTS, FITTERS, Entry
from tourism_twin.models.weighting import Weighting


def _frozen(value: Any) -> Any:
    """Recursively immutable copy: dicts become FrozenDict, lists and tuples become tuples."""
    if isinstance(value, Mapping):
        return FrozenDict(value)
    if isinstance(value, (list, tuple)):
        return tuple(_frozen(v) for v in value)
    return value


class FrozenDict(Mapping):
    """An immutable, hashable, picklable mapping for spec parameters."""

    __slots__ = ("_items",)

    def __init__(self, data: Mapping[str, Any]) -> None:
        object.__setattr__(self, "_items", tuple((key, _frozen(value)) for key, value in data.items()))

    def __getitem__(self, key: str) -> Any:
        for name, value in self._items:
            if name == key:
                return value
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return (name for name, _ in self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __hash__(self) -> int:
        return hash(frozenset(self._items))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Mapping) and dict(self.items()) == dict(other.items())

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("FrozenDict is immutable")

    def __reduce__(self):
        return FrozenDict, (dict(self._items),)

    def __repr__(self) -> str:
        return f"FrozenDict({dict(self._items)!r})"


def _freeze(entry: Entry) -> Entry:
    if isinstance(entry, str):
        return entry
    name, params = entry
    return name, FrozenDict(params)


def _name(entry: Entry) -> str:
    return entry if isinstance(entry, str) else entry[0]


@dataclass(frozen=True)
class ModelSpec:
    """Which components (by registered name), how they are fitted, which training rows count
    (row rules) and how much each counts (weighting)."""

    components: Tuple[Entry, ...]
    fitter: Entry = "backfitting"
    rules: Tuple[RowRule, ...] = ()
    weighting: Optional[Weighting] = None
    options: Tuple[Tuple[str, Any], ...] = ()  # other AdditiveLogModel arguments, as (name, value) pairs

    def __post_init__(self) -> None:
        object.__setattr__(self, "components", tuple(_freeze(e) for e in self.components))
        object.__setattr__(self, "fitter", _freeze(self.fitter))
        object.__setattr__(self, "rules", tuple(self.rules))
        options = self.options.items() if isinstance(self.options, Mapping) else self.options
        object.__setattr__(self, "options", tuple((key, _frozen(value)) for key, value in options))
        for entry in self.components:
            COMPONENTS.factory(_name(entry))  # unknown names fail when the spec is declared
        FITTERS.factory(_name(self.fitter))

    def build(self) -> AdditiveLogModel:
        return AdditiveLogModel([COMPONENTS.build(e) for e in self.components], fitter=FITTERS.build(self.fitter),
                                rules=self.rules, weighting=self.weighting, **dict(self.options))

    def blocks(self) -> List[str]:
        return [COMPONENTS.block(_name(e)) for e in self.components]

    def with_components(self, components: Sequence[Entry]) -> "ModelSpec":
        return replace(self, components=tuple(components))

    def replace_component(self, name: str, entry: Entry) -> "ModelSpec":
        """The same spec with the component registered as `name` swapped for `entry`."""
        if name not in [_name(e) for e in self.components]:
            raise KeyError(f"Spec has no component {name!r}")
        return self.with_components([entry if _name(e) == name else e for e in self.components])

    def without(self, name: str) -> "ModelSpec":
        """The same spec without the component registered as `name` (an ablation)."""
        if name not in [_name(e) for e in self.components]:
            raise KeyError(f"Spec has no component {name!r}")
        return self.with_components([e for e in self.components if _name(e) != name])

    def adding(self, entry: Entry) -> "ModelSpec":
        return self.with_components([*self.components, entry])

    def with_weighting(self, weighting: Optional[Weighting]) -> "ModelSpec":
        return replace(self, weighting=weighting)
