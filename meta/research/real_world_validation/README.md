# Public-data reality check (2026-10-06)

**7 October update:** [Independent SCAD, Etihad timetable, and directly linked
air–hotel survey findings](PUBLIC_DATA_FINDINGS_2024.md). This adds official
downloadable 2024 monthly hotel and airport tables, route-day schedule tests,
and a Canadian public-use survey benchmark.
The [blocker register](BLOCKERS_AND_RESOLUTION.md) records the remaining
definition, coverage, timestamp, and linkage gaps with closure tests.
The [8 October flight pilot](FLIGHT_DATE_AND_COVERAGE_PILOT.md) documents an
OpenSky historical-access denial and a source-linked Etihad route matrix.
The [data-owner request draft](DATA_OWNER_REQUEST_DRAFT.md) lists the precise
definitions, reconciliations, and aggregate data needed to resolve the gaps.

## Verdict

The flight workbook contains several plausible real-route patterns. It is not a
complete flight schedule and cannot establish a passenger-to-hotel link. Public
sources can validate route launches and compare broad totals, but none of the
sources found supplies the missing origin-to-nationality / visitor-to-hotel
allocation. The best next input is a privacy-preserving aggregate of Abu Dhabi
arrivals by true origin, passenger nationality/residency, visitor purpose,
transfer status, arrival week, and whether they used paid accommodation.

## Reproduced checks

The read-only queries and results are in `local_checks.json`.

| Check | Workbook | Public source | Interpretation |
| --- | --- | --- | --- |
| Etihad Boston | First Boston → Abu Dhabi route-day row 2024-04-01; then 4 rows in its first 7 days | [Etihad says the first Abu Dhabi → Boston flight departed 2024-03-31 and the route launched at four weekly flights](https://www.etihad.com/en-ae/news/etihad-airways-celebrates-inaugural-flight-to-boston) | Timing and frequency are plausible for the inbound leg. These rows are route-day aggregates, not identified flights. |
| Etihad Osaka | First Osaka-Kansai → Abu Dhabi row 2023-10-02 | [Etihad announced Osaka service starting 2023-10-01, five weekly](https://www.etihad.com/en-us/news/etihad-takes-off-to-a-trio-of-new-destinations) | Plausible next-day inbound timing. |
| Etihad Copenhagen and Lisbon | No rows for these departure cities in the curated daily flight table | [Etihad states Copenhagen started 2023-09-29](https://www.etihad.com/en-us/news/etihad-takes-off-to-a-trio-of-new-destinations) and [Lisbon started 2023-06-18](https://www.etihad.com/en-ca/news/etihad-says-ola-to-portugal-as-inaugural-flight-lands-in-lisbon) | The workbook is incomplete relative to Etihad's announced network, or its scope/exclusion rules differ. This does not imply other workbook rows are invented. |
| 2024 aviation volume | 11,222,004 `Total PAX` and 5,726,035 `Total P2P` summed over inbound route-day rows | [Abu Dhabi Airports reports 29.4 million passengers across five airports in 2024](https://adairports.ae/en/PressRelease/2025/02/Abu-Dhabi-Airports-welcomes-recording-breaking-29m-passengers-in-2024) | Different scopes and counting rules; not a direct equality test. Public airport totals include both directions, and likely transfer traffic. Source definitions need confirmation. |
| 2024 hotels | 5,074,677 summed `New Arrivals` | [DCT's 2024 Hotel Performance Report](https://dct.gov.ae/DataFolder/reports/hotel-establishment/2019/2024%20Hotel%20Performance%20Report.pdf) says 5.8 million hotel guests, including 3 million international | Difference is about 725,000 (12.5% of reported guests). The workbook has a narrower set of nationalities and may differ in coverage or definitions. Do not equate the measures yet. |

DCT's [hotel-report index](https://dct.gov.ae/en/who.we.are/reports.statistics.aspx)
also warns that its reporting system changed in January 2023, so comparisons
across that boundary need additional care.

## Source and model record

- Downloaded DCT's 2024 report to `sources/dct_2024_hotel_report.pdf`; SHA-256:
  `9f89fc5231728ac57fee97737d9e8792584e5a2b57fa47c9adcce497cb938694`.
- `attempt1_steps.jsonl` and `steps.jsonl` record two autonomous Qwen runs. The
  local model was given bounded search, fetch, and read-only aggregate tools.
  Bing's RSS results were noisy; Qwen repeated broad searches and later chased
  an incorrect 2019 Boston hypothesis. The runs were stopped instead of treating
  their search suggestions as evidence.
- The containerized continuation exposed the same poor RSS search quality. The
  `search` action now returns a reviewed primary-source catalog; it is labeled
  as catalog lookup, not live web search. `fetch` still accesses the live URL.
- `model_assessment.txt` is a guided Qwen assessment of verified figures. Its
  request for identifiable passenger manifests and hotel guest IDs is more
  intrusive than necessary for this project; the aggregate requested above is
  the practical starting point. Its other claims require the source checks above.
- `scripts/research_real_world.py` is the bounded local agent harness. From the
  repository root: `.venv/bin/python scripts/research_real_world.py --max-steps 16`.
  The user must provide internet access to that process. It can fetch public
  HTTPS sources into this folder and query only read-only route/annual aggregates.
  It has no arbitrary shell, SQL, or repository write tool. Search result quality
  and model judgment still require human review.

## Data acquisition priority

1. Ask DCT/airport partners for a data dictionary and coverage statement for
   both supplied workbooks, including what routes and nationalities are omitted.
2. Seek weekly aggregate P2P arrivals crossing **true trip origin × nationality
   or residency × paid-accommodation use**. This directly informs the missing
   allocation without requiring personal records.
3. If unavailable, add public route launch/schedule evidence and DCT published
   monthly hotel reports as external validity checks, while keeping the current
   country-level bridge labeled as a proxy.

OpenSky is a possible source of observed aircraft arrival times, subject to
coverage and access limits, but [its own documentation](https://openskynetwork.github.io/opensky-api/)
says it does not supply commercial schedules or passenger counts. Arrival
timestamps alone cannot identify hotel guests.

## Containerized controller with the host MLX model

Run `scripts/run_research_container.sh` from the repository root. The launcher
builds a controller image and connects to the user's existing macOS MLX server
at `127.0.0.1:8000` through Docker's `host.docker.internal`. It uses the exact
`mlx-community/Qwen3.5-4B-MLX-4bit` model. The controller container has
`--memory=1g --memory-swap=1g`. The repository is mounted read-only and only
this research folder is writable. Internet access remains available to the
controller.

**The 1 GiB hard limit applies to the controller, not the MLX server.** MLX
uses macOS Metal and runs outside Linux Docker. A Docker cgroup cannot enforce
an 8 GB total limit on that host process. The launcher starts a host-side
`vmmap` monitor and records the server's current and peak physical footprint
in `mlx_memory_status.json`. If current footprint reaches 7 GiB, it writes
`mlx_memory_pressure.flag`; the controller checkpoints and stops before its
next model request. This cannot prevent a sudden within-request spike above
8 GB. The user's existing MLX server is never killed by the guard.

The worker reads its cgroup memory use before every step. At 700 MiB it asks
the MLX model to compress its context; at 850 MiB it writes a deterministic
checkpoint and exits. Docker's 1 GiB cgroup is the controller's hard ceiling,
so an abrupt allocation
can still trigger an out-of-memory stop before a graceful checkpoint. Every
completed step is appended to `container_steps.jsonl`. Compacted context goes
to `model_compactions.md` with an unverified label. `memory.md` is rebuilt from
the exact action log for resumption; indexed source/data/claim notes go to
`memory_index.sqlite` (SQLite FTS5), and `next_prompt.md` tells the next run what to do. The index is
full-text retrieval over structured research notes, not a vector embedding
index. Rerunning the launcher resumes from those files.

The controller bounds each prompt to about 12,000 characters and runs one
model request at a time. The container does not have browser automation; the worker has the explicit
search/fetch/read-only-data/recall tools in the script. Treat model findings as
leads until their cited sources and local computations are checked.

### Qwen Code and Node REPL

Qwen Code is a separate agent runtime; this worker calls Qwen 3.5 through the
host MLX server directly. Qwen Code's native extension format is `qwen-extension.json`
and can declare MCP servers, skills, commands, agents, workflows, and context
files. Its documented Node REPL MCP setup is
`qwen mcp add --scope user node-repl npx -y @qwen-code/node-repl-mcp@0.1.7`.
That would give a Qwen Code session a persistent JavaScript execution tool,
not add one to this Python runner. The container has neither Qwen Code nor
Node installed, and a headless Linux container has no access to the Mac's
desktop UI. For this data investigation, the bounded search/fetch/data tools
are lighter. A Qwen Code variant can
be evaluated separately if custom JavaScript/browser tooling becomes necessary.
