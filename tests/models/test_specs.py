"""Declarative specs and the component registry."""

from __future__ import annotations

import pytest
from synthetic import _synthetic


def test_registry_builds_specs_and_covers_every_block():
    from tourism_twin.models.registry import BLOCKS, COMPONENTS
    from tourism_twin.models.spec import ModelSpec
    from tourism_twin.nowcast.specs import DOMESTIC_NOWCAST, INTL_NOWCAST

    assert {COMPONENTS.block(name) for name in COMPONENTS.names()} == set(BLOCKS)
    assert INTL_NOWCAST.blocks() == ["flow", "time", "time", "holiday"]
    assert DOMESTIC_NOWCAST.blocks() == ["flow", "time", "time", "time"]
    first, second = INTL_NOWCAST.build(), INTL_NOWCAST.build()
    assert first.components[0] is not second.components[0]  # every build is a fresh, unfitted model
    with pytest.raises(KeyError, match="Unknown component"):
        ModelSpec(components=("no_such_component",)).build()


def test_spec_builds_share_nothing_and_router_rejects_unserved_rows():
    from tourism_twin.models.spec import ModelSpec
    from tourism_twin.nowcast.routing import MarketRouter

    spec = ModelSpec(components=(("annual_fourier", {"harmonics": 2}), "linear_trend"), fitter="joint_linear")
    with pytest.raises(TypeError):
        spec.components[0][1]["harmonics"] = 9  # entries are frozen: one spec is safe to share
    import copy, pickle
    from tourism_twin.nowcast.specs import INTL_NOWCAST_GBM
    assert pickle.loads(pickle.dumps(INTL_NOWCAST_GBM)) == INTL_NOWCAST_GBM == copy.deepcopy(INTL_NOWCAST_GBM)
    assert len({INTL_NOWCAST_GBM, copy.deepcopy(INTL_NOWCAST_GBM)}) == 1  # hashable: usable as a cache key
    frame = _synthetic()
    first = spec.build().fit(frame)
    assert spec.build().fitted_ == {} and first.fitted_  # every build is a fresh model

    router = MarketRouter(spec.build, spec.build).fit(frame)  # trained on international rows only
    with pytest.raises(KeyError, match="No DOMESTIC model"):
        router.predict(frame.assign(market="DOMESTIC"))
    with pytest.raises(TypeError, match="Cannot build component 'annual_fourier'"):
        ModelSpec(components=(("annual_fourier", {"no_such_param": 1}), "linear_trend")).build()
