# Python API

```python
from tourism_twin.planning.simulator import TourismDigitalTwin
from tourism_twin.domain.scenario import ScenarioLever

twin = TourismDigitalTwin()   # loads the calibrated artifacts from lake/curated/

lever = ScenarioLever(
    market="GERMANY",
    delta_frequency=1.0,      # +1 weekly flight
    aircraft_gauge=250.0,     # seats per added flight
    delta_load_factor=0.03,   # +3 pp load factor
)
report = twin.run_scenario(market="GERMANY", season="Winter_Peak", lever=lever, n_draws=1500)

print(f"Incremental guests: {report.structural_result.delta_guests:+,.0f}")
print(f"P10 lift:           {report.uncertainty_bands.delta_p10:+,.0f}")
print(f"P90 lift:           {report.uncertainty_bands.delta_p90:+,.0f}")
print(report.recommendation_summary)
```

Other `ScenarioLever` fields: `delta_seats_pct`, `delta_p2p_share`, `delta_multiplier_pct`, `delta_los` (`src/tourism_twin/domain/scenario.py`).
