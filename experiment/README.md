# Experiments

One folder per experiment: code, a README with the question and conclusion, and aggregate results. Cached outputs go to `<name>/out/`, which git ignores.

- `eda_coupling/` : how seats, P2P, arrivals and guests move together after time is removed, and at which lag (descriptive)
- `level_memory/` : can error carry-forward or a drifting guests-per-arrival strength use the memory in the nowcast and chain errors?
- `load_factor_link/` : does a learned seats-to-passengers link (load factor response) in front of the planning chain improve guests and the seat lever?
- `scenario_response/` : how well do LINEAR, the shipped S-curve adjustments, a learned short-run elasticity and the seat chain predict guests when a market's seats change, against a calendar-only null?
