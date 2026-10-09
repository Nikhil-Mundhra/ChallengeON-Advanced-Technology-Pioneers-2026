"""Component and fitter registries: name -> factory, declared once and requested by name
(the same pattern as features/registry.py). ModelSpec (models/spec.py) builds models from them.

Adding an axis: register one component here, then list its name in a ModelSpec.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Generic, List, Mapping, Tuple, TypeVar, Union

from tourism_twin.models.components import (
    AnnualFourier,
    ArrivalsConvolution,
    CentredSlope,
    DayOfWeek,
    EventKernel,
    GroupScale,
    LinearRegressors,
    LinearTrend,
    LocalLevel,
    ResidualGBM,
)
from tourism_twin.models.components.base import Component
from tourism_twin.models.fitters import Backfitting, JointLinear

BLOCKS = ("flow", "time", "holiday", "flight", "residual")  # docs/model_design.md §3.1

Entry = Union[str, Tuple[str, Mapping[str, Any]]]  # a registered name, or (name, constructor params)
T = TypeVar("T")


class Registry(Generic[T]):
    """Name → factory, for components or fitters."""

    def __init__(self, kind: str) -> None:
        self.kind = kind
        self._factories: Dict[str, Callable[..., T]] = {}

    def register(self, name: str, factory: Callable[..., T]) -> Callable[..., T]:
        if name in self._factories:
            raise ValueError(f"{self.kind} {name!r} is already registered")
        self._factories[name] = factory
        return factory

    def names(self) -> List[str]:
        return sorted(self._factories)

    def factory(self, name: str) -> Callable[..., T]:
        if name not in self._factories:
            raise KeyError(f"Unknown {self.kind} {name!r}; registered: {self.names()}")
        return self._factories[name]

    def build(self, entry: Entry) -> T:
        name, params = (entry, {}) if isinstance(entry, str) else entry
        factory = self.factory(name)
        try:
            return factory(**params)
        except TypeError as error:
            raise TypeError(f"Cannot build {self.kind} {name!r} with {dict(params)}: {error}") from error


class ComponentRegistry(Registry[Component]):
    def register(self, name: str, factory: Callable[..., Component]) -> Callable[..., Component]:
        block = getattr(factory, "group", None)
        if block not in BLOCKS:
            raise ValueError(f"Component {name!r} has group {block!r}; expected one of {BLOCKS}")
        return super().register(name, factory)

    def block(self, name: str) -> str:
        return self.factory(name).group


COMPONENTS = ComponentRegistry("component")
COMPONENTS.register("arrivals_kernel", ArrivalsConvolution)   # flow
COMPONENTS.register("local_level", LocalLevel)                # time
COMPONENTS.register("linear_trend", LinearTrend)              # time
COMPONENTS.register("slope", CentredSlope)                    # time
COMPONENTS.register("annual_fourier", AnnualFourier)          # time
COMPONENTS.register("weekday", DayOfWeek)                     # time
COMPONENTS.register("events", EventKernel)                    # holiday
COMPONENTS.register("group_scale", GroupScale)                # flow (per-series scale in a pooled fit)
COMPONENTS.register("regressors", LinearRegressors)           # flight
COMPONENTS.register("residual_gbm", ResidualGBM)              # residual

FITTERS: Registry[Any] = Registry("fitter")
FITTERS.register("backfitting", Backfitting)
FITTERS.register("joint_linear", JointLinear)
