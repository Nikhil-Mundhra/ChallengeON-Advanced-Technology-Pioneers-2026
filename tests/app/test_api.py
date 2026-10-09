"""Web API."""

from __future__ import annotations


def test_api_rejects_an_invalid_season_and_serves_a_scenario():
    from app.server import DigitalTwinHandler

    class Recorder:
        def send_json(self, data, status=200):
            self.response, self.status = data, status

    handler = Recorder()
    DigitalTwinHandler.handle_simulate(handler, {"market": ["UNITED KINGDOM"], "season": ["InvalidSeason"]})
    assert handler.status == 400
    DigitalTwinHandler.handle_simulate(handler, {"market": ["UNITED KINGDOM"], "season": ["Winter_Peak"], "delta_freq": [2]})
    assert handler.status == 200 and handler.response["hybrid"]["is_monotonic"]
