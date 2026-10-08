{
  "checklist_version": "1.0",
  "repository_root": "/Users/nikhilmundhra/Documents/Github/Hackathons/ChallengeON-Advanced-Technology-Pioneers-2026",
  "generated_at": "2026-09-30T22:27:47+04:00",
  "generation_basis": {
    "inspected_paths": [
      "AGENTS.md instructions supplied with the request",
      ".agents/skills/dct-tourism-hackathon-reviewer/SKILL.md",
      ".agents/skills/dct-tourism-hackathon-reviewer/references/challenge-brief.md",
      ".agents/skills/dct-tourism-hackathon-reviewer/references/repository-audit.md",
      ".agents/skills/data-quality-and-contract-testing/SKILL.md",
      ".agents/skills/data-reconciliation-and-financial-controls/SKILL.md",
      "01a - DCT Dataset/Data_Dictionary.pdf",
      "01a - DCT Dataset/*.xlsx",
      "lake/manifest.json",
      "lake/analytics.duckdb",
      "lake/curated/*.parquet",
      "lake/curated/*.json",
      "lake/curated/residual_engine.pkl",
      "scripts/*.py",
      "src/engine/*.py",
      "src/app/server.py",
      "src/app/static/index.html",
      "tests/test_digital_twin.py",
      "README.md",
      "docs/*.md",
      "sql/example_queries.sql",
      "output/",
      "tmp/",
      ".gitignore",
      "git status and tracked-file inventory"
    ],
    "unavailable_paths": [
      "DATA_ISSUES_GEMMA.md"
    ],
    "assumptions": [
      "All checklist execution is read-only; temporary evidence may be written only beneath a dedicated directory outside project artifacts.",
      "DuckDB must be opened read-only and pickle inspection must occur in an isolated local process because pickle loading executes code.",
      "Exact business thresholds not defined by source contracts must be reported as distributions requiring owner confirmation.",
      "The delivered workbooks and PDF are the authoritative local source package for offline checks.",
      "The observed working tree contains pre-existing modifications to seven curated artifacts; auditors must preserve and identify this state."
    ],
    "known_limitations": [
      "This generation performed structural inspection and metadata discovery, not the full audit.",
      "Workbook metadata, schemas, table names, source hashes, and artifact structures were inspected, but every cell and every generated-report page was not audited.",
      "No external challenge page was queried because the requested checklist must be executable without network access.",
      "No repository file, data artifact, model artifact, or issue register was modified."
    ]
  },
  "coverage_matrix": [
    {
      "domain": "A",
      "task_ids": ["INV-001", "INV-002", "INV-003"],
      "coverage_notes": "Repository, Git, generated assets, database objects, and provenance inventory."
    },
    {
      "domain": "B",
      "task_ids": ["RAW-001", "RAW-002", "RAW-003"],
      "coverage_notes": "Workbook structure, raw contracts, PDF definitions, and train/test drift."
    },
    {
      "domain": "C",
      "task_ids": ["SCH-001", "SCH-002", "SCH-003"],
      "coverage_notes": "Readability, schema fidelity, parsing loss, precision, and artifact compatibility."
    },
    {
      "domain": "D",
      "task_ids": ["KEY-001", "KEY-002", "KEY-003", "KEY-004"],
      "coverage_notes": "Keys, duplicates, grains, join cardinality, and incomplete-period behavior."
    },
    {
      "domain": "E",
      "task_ids": ["TEMP-001", "TEMP-002", "TEMP-003", "TEMP-004"],
      "coverage_notes": "Coverage, continuity, grain transitions, weekly boundaries, and future leakage."
    },
    {
      "domain": "F",
      "task_ids": ["MISS-001", "MISS-002", "MISS-003"],
      "coverage_notes": "Cell and row missingness, status semantics, imputation, and split drift."
    },
    {
      "domain": "G",
      "task_ids": ["NUM-001", "NUM-002", "NUM-003", "NUM-004"],
      "coverage_notes": "Physical identities, bounds, integer validity, outliers, and clipping."
    },
    {
      "domain": "H",
      "task_ids": ["CAT-001", "CAT-002", "CAT-003"],
      "coverage_notes": "Category normalization, temporal drift, mappings, clusters, and archetypes."
    },
    {
      "domain": "I",
      "task_ids": ["BRG-001", "BRG-002", "BRG-003", "BRG-004"],
      "coverage_notes": "Origin-nationality semantics, identifiability, fallback, and sensitivity."
    },
    {
      "domain": "J",
      "task_ids": ["AGG-001", "AGG-002", "AGG-003", "AGG-004"],
      "coverage_notes": "Aggregation operators, denominators, OTHER handling, rounding, and dominance."
    },
    {
      "domain": "K",
      "task_ids": ["REC-001", "REC-002", "REC-003", "REC-004", "REC-005", "REC-006", "REC-007"],
      "coverage_notes": "Stage-by-stage reconciliations from Excel through UI, including exception evidence."
    },
    {
      "domain": "L",
      "task_ids": ["LIN-001", "LIN-002", "LIN-003"],
      "coverage_notes": "Field lineage, feature derivation, fit windows, defaults, and dead fields."
    },
    {
      "domain": "M",
      "task_ids": ["LEAK-001", "LEAK-002", "LEAK-003", "LEAK-004"],
      "coverage_notes": "Split membership, preprocessing leakage, decision-time availability, and calibration reuse."
    },
    {
      "domain": "N",
      "task_ids": ["MET-001", "MET-002", "MET-003", "MET-004"],
      "coverage_notes": "Target semantics, metric reproduction, segment weighting, and baseline parity."
    },
    {
      "domain": "O",
      "task_ids": ["STAT-001", "STAT-002", "STAT-003"],
      "coverage_notes": "Distribution shift, sparsity, instability, residual diagnostics, and ablations."
    },
    {
      "domain": "P",
      "task_ids": ["UNC-001", "UNC-002", "UNC-003", "UNC-004"],
      "coverage_notes": "Calibration separation, coverage, bounded/correlated draws, residual dependence, and claim meaning."
    },
    {
      "domain": "Q",
      "task_ids": ["SCEN-001", "SCEN-002", "SCEN-003", "SCEN-004"],
      "coverage_notes": "Baseline invariance, monotonicity, physical bounds, waterfall identity, and adversarial API cases."
    },
    {
      "domain": "R",
      "task_ids": ["REPRO-001", "REPRO-002", "REPRO-003", "REPRO-004"],
      "coverage_notes": "Manifest integrity, deterministic rebuilds, serialization compatibility, and local-state reliance."
    },
    {
      "domain": "S",
      "task_ids": ["CONS-001", "CONS-002", "CONS-003", "CONS-004"],
      "coverage_notes": "Metrics, windows, counts, definitions, defaults, uncertainty, and mode labels across surfaces."
    },
    {
      "domain": "T",
      "task_ids": ["TEST-001", "TEST-002", "TEST-003"],
      "coverage_notes": "Test inventory, tautology review, missing contracts, fixtures, and end-to-end evidence."
    },
    {
      "domain": "U",
      "task_ids": ["SEC-001", "SEC-002", "SEC-003"],
      "coverage_notes": "Restricted-data exposure through Git, static/API surfaces, reports, logs, and caches."
    },
    {
      "domain": "V",
      "task_ids": ["DOC-001", "DOC-002", "DOC-003"],
      "coverage_notes": "Unsupported claims, undocumented behavior, causal language, stale material, and owner questions."
    },
    {
      "domain": "W",
      "task_ids": ["VS-001", "VS-002", "VS-003", "VS-004", "VS-005", "VS-006", "VS-007", "VS-008"],
      "coverage_notes": "Eight required end-to-end slices spanning volume, sparsity, hubs, pooled markets, domestic, cold start, split boundaries, and missingness."
    }
  ],
  "execution_order": [
    {
      "phase": 1,
      "name": "Inventory and contracts",
      "task_ids": ["INV-001", "INV-002", "INV-003", "RAW-001", "RAW-002", "RAW-003", "SCH-001", "SCH-002", "SCH-003"],
      "reason": "Establish the authoritative asset set, schemas, hashes, and source meanings."
    },
    {
      "phase": 2,
      "name": "Native data integrity",
      "task_ids": ["KEY-001", "KEY-002", "KEY-003", "KEY-004", "TEMP-001", "TEMP-002", "TEMP-003", "TEMP-004", "MISS-001", "MISS-002", "MISS-003", "NUM-001", "NUM-002", "NUM-003", "NUM-004", "CAT-001", "CAT-002", "CAT-003"],
      "reason": "Prove grain, temporal, missingness, numeric, and entity contracts before trusting transformations."
    },
    {
      "phase": 3,
      "name": "Semantic bridge and aggregation",
      "task_ids": ["BRG-001", "BRG-002", "BRG-003", "BRG-004", "AGG-001", "AGG-002", "AGG-003", "AGG-004", "LIN-001", "LIN-002", "LIN-003"],
      "reason": "Resolve the core origin-nationality assumption and transformation semantics."
    },
    {
      "phase": 4,
      "name": "Source-to-target controls",
      "task_ids": ["REC-001", "REC-002", "REC-003", "REC-004", "REC-005", "REC-006", "REC-007"],
      "reason": "Independently reconcile every major lifecycle transition and retain exceptions."
    },
    {
      "phase": 5,
      "name": "Model validity",
      "task_ids": ["LEAK-001", "LEAK-002", "LEAK-003", "LEAK-004", "MET-001", "MET-002", "MET-003", "MET-004", "STAT-001", "STAT-002", "STAT-003", "UNC-001", "UNC-002", "UNC-003", "UNC-004"],
      "reason": "Assess information availability, evaluation validity, model stability, and uncertainty."
    },
    {
      "phase": 6,
      "name": "Product behavior and reproducibility",
      "task_ids": ["SCEN-001", "SCEN-002", "SCEN-003", "SCEN-004", "REPRO-001", "REPRO-002", "REPRO-003", "REPRO-004", "TEST-001", "TEST-002", "TEST-003"],
      "reason": "Exercise scenario invariants, artifacts, rebuild behavior, and actual test coverage."
    },
    {
      "phase": 7,
      "name": "Claims, exposure, and vertical slices",
      "task_ids": ["CONS-001", "CONS-002", "CONS-003", "CONS-004", "SEC-001", "SEC-002", "SEC-003", "DOC-001", "DOC-002", "DOC-003", "VS-001", "VS-002", "VS-003", "VS-004", "VS-005", "VS-006", "VS-007", "VS-008"],
      "reason": "Compare public surfaces and trace representative records through the complete system."
    }
  ],
  "tasks": [
    {
      "id": "INV-001",
      "domain": "A. Repository and asset inventory",
      "title": "Enumerate every audit-relevant repository asset",
      "priority": "P1",
      "objective": "What files, directories, generated outputs, caches, databases, reports, figures, and local-only artifacts exist?",
      "risk": "Uninventoried assets can hide stale evidence, restricted data, or alternate implementations.",
      "scope": {
        "files": ["**/*", ".gitignore", ".git/"],
        "tables_or_sheets": ["DISCOVER"],
        "fields": ["path", "size", "mtime", "Git status", "tracked", "ignored"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["NONE"],
      "procedure": [
        "List regular files including hidden and ignored files, excluding file contents under .git.",
        "Record size, modification time, Git tracked/ignored/status state, extension, and inferred role.",
        "Classify each as raw source, source code, curated artifact, model artifact, documentation, report, cache, or unknown."
      ],
      "suggested_commands": ["rg --files --hidden; git ls-files; git status --short; git check-ignore -v <path>; find . -type f -maxdepth 6 -print"],
      "assertions": ["Every discovered artifact has one explicit classification.", "Unknown, orphaned, duplicated, or unexpectedly committed artifacts are listed separately."],
      "reconciliation": {
        "source_measure": "filesystem file count",
        "target_measure": "classified inventory count",
        "grain": "path",
        "tolerance": "0 unclassified discovered files, excluding .git internals and virtual-environment packages"
      },
      "evidence_required": ["Machine-readable inventory", "Git status excerpt", "Exception list with paths"],
      "completion_criteria": ["All discovered files are classified and exceptions carry an evidence classification."],
      "possible_issue_fingerprints": ["asset:orphaned:<path>", "asset:stale:<path>", "asset:unexpectedly-committed:<path>"],
      "estimated_effort": "medium"
    },
    {
      "id": "INV-002",
      "domain": "A. Repository and asset inventory",
      "title": "Inventory DuckDB, Parquet, JSON, and pickle objects",
      "priority": "P1",
      "objective": "Which tables, views, columns, row groups, JSON keys, and serialized model types actually exist?",
      "risk": "Documentation may describe assets that differ from consumable artifacts.",
      "scope": {
        "files": ["lake/analytics.duckdb", "lake/curated/*"],
        "tables_or_sheets": ["flight_all", "flight_daily", "flight_monthly", "flight_daily_totals", "guest_daily", "guest_actuals", "guest_prediction_rows", "guest_daily_totals", "guest_flight_daily", "DISCOVER"],
        "fields": ["DISCOVER"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["INV-001"],
      "procedure": [
        "Open DuckDB read-only and enumerate schemas, tables, views, definitions, counts, and columns.",
        "Read Parquet metadata and JSON structures without rewriting them.",
        "Inspect pickle opcode/type metadata in an isolated process without trusting it as evidence of model correctness."
      ],
      "suggested_commands": ["duckdb -readonly lake/analytics.duckdb", "python -m pickletools lake/curated/residual_engine.pkl"],
      "assertions": ["Every database and file artifact has an observed schema and consumer.", "No undocumented table, view, or artifact remains unexplained."],
      "reconciliation": {
        "source_measure": "discovered structured artifacts",
        "target_measure": "schema inventory records",
        "grain": "artifact/object",
        "tolerance": "exact one-to-one inventory coverage"
      },
      "evidence_required": ["DESCRIBE output", "View definitions", "Parquet metadata", "JSON key tree", "Pickle protocol and top-level type"],
      "completion_criteria": ["All structured artifacts and objects are inventoried without mutation."],
      "possible_issue_fingerprints": ["artifact:undocumented-object:<name>", "artifact:no-consumer:<name>", "artifact:schema-mismatch:<name>"],
      "estimated_effort": "medium"
    },
    {
      "id": "INV-003",
      "domain": "A. Repository and asset inventory",
      "title": "Compare documented assets with the discovered inventory",
      "priority": "P2",
      "objective": "Do README, guides, manifest, Makefile, and report builders name the same assets that exist?",
      "risk": "Missing or stale asset descriptions make reproduction and review unreliable.",
      "scope": {
        "files": ["README.md", "docs/*.md", "lake/manifest.json", "Makefile", "scripts/build_*report.py", "output/**/*"],
        "tables_or_sheets": ["NOT_APPLICABLE"],
        "fields": ["paths", "commands", "row counts", "artifact roles"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["INV-001", "INV-002"],
      "procedure": [
        "Extract every path and generated-artifact claim from documentation and build scripts.",
        "Match each claim to the inventory and identify undocumented or nonexistent paths.",
        "Distinguish committed, ignored, generated, and raw-restricted assets."
      ],
      "suggested_commands": ["rg -n 'lake/|output/|\\.parquet|\\.json|\\.pkl|\\.duckdb|\\.xlsx|\\.pdf' README.md docs Makefile scripts"],
      "assertions": ["Every documented required artifact exists or is explicitly generated.", "Every material discovered artifact has documented provenance."],
      "reconciliation": {
        "source_measure": "documented asset references",
        "target_measure": "inventory matches",
        "grain": "normalized path",
        "tolerance": "0 unexplained missing required assets"
      },
      "evidence_required": ["Claim-to-path matrix", "file:line citations", "Missing and undocumented lists"],
      "completion_criteria": ["All mismatches are recorded without treating documentation as authoritative evidence."],
      "possible_issue_fingerprints": ["docs:missing-asset:<path>", "docs:undocumented-artifact:<path>", "provenance:unclear:<path>"],
      "estimated_effort": "small"
    },
    {
      "id": "RAW-001",
      "domain": "B. Raw workbook and PDF contract discovery",
      "title": "Profile workbook physical structure",
      "priority": "P1",
      "objective": "What sheets, headers, dimensions, formulas, merged cells, hidden objects, filters, named ranges, and non-tabular regions are delivered?",
      "risk": "Invisible or non-tabular workbook structure can cause silent ingestion loss.",
      "scope": {
        "files": ["01a - DCT Dataset/*.xlsx"],
        "tables_or_sheets": ["Export", "DISCOVER"],
        "fields": ["ALL CELLS"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["INV-001"],
      "procedure": [
        "Open every workbook without recalculation and enumerate workbook and sheet metadata.",
        "Inspect formulas, merged ranges, hidden sheets/rows/columns, filters, named ranges, blank/duplicate headers, and populated cells beyond the detected table.",
        "Retain representative exceptions with workbook, sheet, and cell coordinates."
      ],
      "suggested_commands": ["Use openpyxl in read-only inspection mode and zipinfo for XLSX package members."],
      "assertions": ["Ingested tabular ranges include every intended row and column.", "No hidden or formula-driven content is silently ignored."],
      "reconciliation": {
        "source_measure": "non-empty workbook cells",
        "target_measure": "cells inside identified source tables plus documented non-tabular cells",
        "grain": "workbook/sheet/cell",
        "tolerance": "0 unexplained populated cells"
      },
      "evidence_required": ["Sheet metadata table", "header list", "cell-coordinate exception samples"],
      "completion_criteria": ["Every workbook structure feature is reported, including confirmed zero counts."],
      "possible_issue_fingerprints": ["raw:hidden-content:<file>:<sheet>", "raw:duplicate-header:<file>:<header>", "raw:out-of-table-content:<file>"],
      "estimated_effort": "medium"
    },
    {
      "id": "RAW-002",
      "domain": "B. Raw workbook and PDF contract discovery",
      "title": "Derive the delivered raw data contract",
      "priority": "P1",
      "objective": "What are the observed columns, types, row counts, date ranges, candidate keys, units, null behavior, and status markers in each workbook?",
      "risk": "Downstream assumptions cannot be assessed without a source-level contract.",
      "scope": {
        "files": ["01a - DCT Dataset/*.xlsx"],
        "tables_or_sheets": ["Export"],
        "fields": ["Date", "Guests", "New Arrivals", "Same-Day Guests", "Nationality", "Residence (groups)", "Departure Country Name", "Departure City", "Arrival City", "Airline Name", "Average Weekly Frequency", "Load Factor", "Total P2P", "Total PAX", "Total Seats", "Total Transfer", "Total Transit", "DISCOVER"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["RAW-001"],
      "procedure": [
        "Profile types, nulls, exact and normalized labels, numeric ranges, row counts, and date coverage per file.",
        "Infer candidate keys but label them observed rather than official.",
        "Separate train/test and domestic/international contracts."
      ],
      "suggested_commands": ["Read each sheet with pandas using dtype-preserving options; emit summaries only to the temporary audit directory."],
      "assertions": ["Every raw field has an observed type and null/status profile.", "Candidate keys and source grain are explicitly stated with evidence."],
      "reconciliation": {
        "source_measure": "worksheet data rows",
        "target_measure": "profiled rows",
        "grain": "file/sheet",
        "tolerance": "exact row count excluding one identified header row"
      },
      "evidence_required": ["Per-file contract table", "min/max dates", "type-frequency tables", "candidate-key duplicate counts"],
      "completion_criteria": ["All five workbooks have complete observed contracts."],
      "possible_issue_fingerprints": ["raw:contract-unknown:<file>:<field>", "raw:grain-ambiguous:<file>", "raw:key-nonunique:<file>:<key>"],
      "estimated_effort": "large"
    },
    {
      "id": "RAW-003",
      "domain": "B. Raw workbook and PDF contract discovery",
      "title": "Compare Data Dictionary definitions to delivered files",
      "priority": "P1",
      "objective": "Does the PDF agree with actual headers, units, grain, keys, nulls, date ranges, split roles, and allowed values?",
      "risk": "A schema can parse successfully while violating the provider's intended meaning.",
      "scope": {
        "files": ["01a - DCT Dataset/Data_Dictionary.pdf", "01a - DCT Dataset/*.xlsx"],
        "tables_or_sheets": ["Export", "PDF field definitions"],
        "fields": ["DISCOVER"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["RAW-002"],
      "procedure": [
        "Extract PDF text and tables while retaining page references.",
        "Create a field-by-field comparison with the observed raw contract.",
        "Record undocumented delivered fields, documented missing fields, contradictions, and definitions requiring owner confirmation."
      ],
      "suggested_commands": ["pdftotext -layout '01a - DCT Dataset/Data_Dictionary.pdf' -"],
      "assertions": ["Every delivered field maps to one PDF definition or an explicit documentation gap.", "Units and status semantics are not inferred when the PDF is silent."],
      "reconciliation": {
        "source_measure": "PDF-defined fields",
        "target_measure": "delivered headers",
        "grain": "dataset/field",
        "tolerance": "exact label mapping after explicitly documented normalization"
      },
      "evidence_required": ["PDF page citations", "field comparison matrix", "owner-question list"],
      "completion_criteria": ["Every discrepancy is classified as supported, ambiguous, missing, or contradicted."],
      "possible_issue_fingerprints": ["contract:pdf-file-mismatch:<dataset>:<field>", "contract:unit-ambiguous:<field>", "contract:status-undefined:<field>"],
      "estimated_effort": "medium"
    },
    {
      "id": "SCH-001",
      "domain": "C. File and schema integrity",
      "title": "Verify source and artifact readability without coercion",
      "priority": "P1",
      "objective": "Can every source and product be opened by its intended reader without repair, warnings, or silent coercion?",
      "risk": "Corrupt or reader-dependent files invalidate reproducibility.",
      "scope": {
        "files": ["01a - DCT Dataset/*", "lake/analytics.duckdb", "lake/curated/*"],
        "tables_or_sheets": ["ALL"],
        "fields": ["ALL"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["INV-002", "RAW-001"],
      "procedure": [
        "Open XLSX, PDF, Parquet, JSON, and DuckDB using independent read-only readers.",
        "Validate container signatures, Parquet footers, JSON syntax, and DuckDB integrity.",
        "Record library versions and every warning or failure."
      ],
      "suggested_commands": ["file <path>; unzip -t <xlsx>; parquet-tools meta <parquet>; jq empty <json>; duckdb -readonly lake/analytics.duckdb 'PRAGMA database_size'"],
      "assertions": ["Every required artifact is readable.", "No reader silently drops malformed rows or fields."],
      "reconciliation": {
        "source_measure": "required artifact count",
        "target_measure": "successfully validated artifact count",
        "grain": "file",
        "tolerance": "0 failures"
      },
      "evidence_required": ["Reader/version log", "validation output", "failure and warning list"],
      "completion_criteria": ["Every required artifact has a reproducible readability result."],
      "possible_issue_fingerprints": ["file:unreadable:<path>", "file:reader-warning:<path>", "file:truncated:<path>"],
      "estimated_effort": "small"
    },
    {
      "id": "SCH-002",
      "domain": "C. File and schema integrity",
      "title": "Measure parsing and type-coercion loss",
      "priority": "P1",
      "objective": "Do ingestion conversions preserve raw values, dates, numeric precision, and status strings?",
      "risk": "Coercion can turn malformed values into nulls, round counts, or misparse dates.",
      "scope": {
        "files": ["scripts/build_lake.py", "01a - DCT Dataset/*.xlsx", "lake/curated/guest_daily.parquet", "lake/curated/flight_daily.parquet", "lake/curated/flight_monthly.parquet"],
        "tables_or_sheets": ["Export"],
        "fields": ["Date", "all numeric fields", "all categorical fields"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["RAW-002", "SCH-001"],
      "procedure": [
        "Inspect parsing, coercion, rounding, fill, and rename code.",
        "For each field, compare raw nonblank values with parsed values using stable row keys.",
        "Report values changed, rejected, rounded, overflowed, or converted to null."
      ],
      "suggested_commands": ["rg -n 'to_datetime|to_numeric|astype|fillna|round|replace|errors=' scripts/build_lake.py"],
      "assertions": ["Every value-changing conversion is documented and counted.", "Counts remain integral and numeric precision is sufficient for identities."],
      "reconciliation": {
        "source_measure": "raw nonblank cells",
        "target_measure": "parsed values plus enumerated rejected cells",
        "grain": "file/row/field",
        "tolerance": "0 unexplained conversions; numeric comparison exact for integers and within 1e-12 for stored ratios"
      },
      "evidence_required": ["Conversion-line citations", "before/after samples", "loss counts by field"],
      "completion_criteria": ["All coercion differences are explained or reported as exceptions."],
      "possible_issue_fingerprints": ["parse:coercion-loss:<file>:<field>", "parse:date-ambiguity:<file>", "parse:precision-loss:<field>"],
      "estimated_effort": "large"
    },
    {
      "id": "SCH-003",
      "domain": "C. File and schema integrity",
      "title": "Check schema drift and serialized-artifact compatibility",
      "priority": "P1",
      "objective": "Are schemas compatible across splits, periods, database tables, Parquet files, JSON consumers, and the residual pickle?",
      "risk": "Stale models or drifted schemas may load yet produce incorrect outputs.",
      "scope": {
        "files": ["01a - DCT Dataset/*.xlsx", "lake/**/*", "src/engine/*.py", "src/app/server.py", "requirements.txt"],
        "tables_or_sheets": ["ALL"],
        "fields": ["DISCOVER"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["INV-002", "RAW-002"],
      "procedure": [
        "Compare train/test and domestic/international source schemas.",
        "Compare database and Parquet schemas and consumer expectations.",
        "Inspect JSON/pickle loading code, package versions, feature names, and compatibility guards."
      ],
      "suggested_commands": ["rg -n 'read_parquet|json.load|pickle|joblib|feature_names|schema|version' engine scripts app requirements.txt"],
      "assertions": ["All intentional schema differences are handled explicitly.", "Serialized artifacts carry enough metadata to reject incompatible consumers."],
      "reconciliation": {
        "source_measure": "producer schema",
        "target_measure": "consumer-required schema",
        "grain": "artifact/field",
        "tolerance": "exact required-field and compatible-type match"
      },
      "evidence_required": ["Schema diff", "producer/consumer citations", "runtime/package compatibility evidence"],
      "completion_criteria": ["Every structured artifact has an explicit compatibility verdict."],
      "possible_issue_fingerprints": ["schema:drift:<source>:<target>:<field>", "artifact:no-version-guard:<path>", "artifact:feature-order-risk:<path>"],
      "estimated_effort": "medium"
    },
    {
      "id": "KEY-001",
      "domain": "D. Keys, duplicates, and grain",
      "title": "Validate guest keys and native grain",
      "priority": "P1",
      "objective": "Are raw and curated guest rows unique at their claimed date-nationality or domestic-date grain?",
      "risk": "Duplicate or conflicting guest keys directly distort targets and metrics.",
      "scope": {
        "files": ["01a - DCT Dataset/data *train.xlsx", "01a - DCT Dataset/data *test.xlsx", "lake/curated/guest_daily.parquet"],
        "tables_or_sheets": ["Export", "guest_daily", "guest_actuals", "guest_prediction_rows"],
        "fields": ["date", "nationality", "residence_group", "dataset_split", "guests", "new_arrivals", "same_day_guests"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["RAW-002", "SCH-002"],
      "procedure": [
        "Test candidate keys separately by file and residence group.",
        "Separate exact duplicate rows from conflicting duplicate keys.",
        "Check whether grid expansion creates only flagged absent rows."
      ],
      "suggested_commands": ["Run GROUP BY candidate-key HAVING COUNT(*)>1 in raw profiles and DuckDB."],
      "assertions": ["Observed guest source keys are unique or every duplicate is characterized.", "Curated grid keys are unique across split boundaries."],
      "reconciliation": {
        "source_measure": "distinct source guest keys",
        "target_measure": "curated is_source_present keys",
        "grain": "date/residence_group/nationality/dataset_split",
        "tolerance": "exact"
      },
      "evidence_required": ["Duplicate counts", "conflicting-key samples", "key definition"],
      "completion_criteria": ["Every duplicate candidate key is enumerated and classified."],
      "possible_issue_fingerprints": ["key:guest-duplicate:<key>", "key:guest-conflict:<key>", "grain:guest-ambiguous"],
      "estimated_effort": "medium"
    },
    {
      "id": "KEY-002",
      "domain": "D. Keys, duplicates, and grain",
      "title": "Validate flight keys and 2022-to-2023 grain transition",
      "priority": "P0",
      "objective": "What uniquely identifies flight rows, and is monthly 2022 data kept separate from daily 2023+ data?",
      "risk": "Treating month-start observations as daily can create severe temporal and volume distortion.",
      "scope": {
        "files": ["01a - DCT Dataset/flight_data.xlsx", "lake/curated/flight_daily.parquet", "lake/curated/flight_monthly.parquet"],
        "tables_or_sheets": ["Export", "flight_all", "flight_daily", "flight_monthly"],
        "fields": ["date", "departure_country_name", "departure_city", "arrival_city", "airline_name", "destination", "source_grain"],
        "date_or_population": "2022-01-01 through maximum date"
      },
      "prerequisites": ["RAW-002", "SCH-002"],
      "procedure": [
        "Discover minimal candidate keys by year and source grain.",
        "Enumerate exact and conflicting duplicates.",
        "Confirm that 12 distinct 2022 month-start dates do not enter flight_daily or weekly joins."
      ],
      "suggested_commands": ["Query key multiplicities by source_grain and year in read-only DuckDB."],
      "assertions": ["Daily and monthly grains are explicit and mutually exclusive.", "No monthly row is interpreted as one operating day."],
      "reconciliation": {
        "source_measure": "raw flight rows by source_grain",
        "target_measure": "flight_daily plus flight_monthly rows",
        "grain": "source row",
        "tolerance": "exact row partition"
      },
      "evidence_required": ["Candidate-key analysis", "duplicate samples", "grain partition counts"],
      "completion_criteria": ["Every flight row has one grain and one curated destination."],
      "possible_issue_fingerprints": ["grain:monthly-as-daily:2022", "key:flight-duplicate:<key>", "key:flight-conflict:<key>"],
      "estimated_effort": "medium"
    },
    {
      "id": "KEY-003",
      "domain": "D. Keys, duplicates, and grain",
      "title": "Measure join cardinality and row multiplication",
      "priority": "P0",
      "objective": "Do guest-flight and market mappings create one-to-many or many-to-many fan-out?",
      "risk": "Join multiplication can fabricate seats, passengers, arrivals, or demand.",
      "scope": {
        "files": ["scripts/build_lake.py", "src/engine/panel.py"],
        "tables_or_sheets": ["guest_daily", "flight_daily", "guest_flight_daily", "weekly_market_panel"],
        "fields": ["date", "market", "nationality", "departure_country_name", "dataset_split"],
        "date_or_population": "2023 onward"
      },
      "prerequisites": ["KEY-001", "KEY-002", "CAT-002"],
      "procedure": [
        "Record row and distinct-key counts before and after every join.",
        "Compute matched, unmatched, and multiply matched keys.",
        "Compare control totals before and after joins at date and market-date grain."
      ],
      "suggested_commands": ["Use read-only SQL CTEs that compare pre-join and post-join key multiplicity and sums."],
      "assertions": ["Each join has an explicitly valid cardinality.", "Flight totals are not repeated for each guest market or split."],
      "reconciliation": {
        "source_measure": "pre-join seats, pax, P2P, guests, arrivals",
        "target_measure": "post-join corresponding totals",
        "grain": "date and market-date",
        "tolerance": "exact, except explicitly enumerated unmatched records"
      },
      "evidence_required": ["Join-cardinality table", "unmatched keys", "multiply matched records", "control totals"],
      "completion_criteria": ["Every join is proven cardinality-safe or has complete exceptions."],
      "possible_issue_fingerprints": ["join:fanout:<stage>:<key>", "join:row-loss:<stage>:<key>", "join:split-duplication:<date>"],
      "estimated_effort": "large"
    },
    {
      "id": "KEY-004",
      "domain": "D. Keys, duplicates, and grain",
      "title": "Validate weekly panel grain and partial periods",
      "priority": "P1",
      "objective": "Is weekly_market_panel unique by week_start, market, and split, with boundary weeks represented correctly?",
      "risk": "Partial or split-crossing weeks can contaminate evaluation and aggregate totals.",
      "scope": {
        "files": ["src/engine/panel.py", "lake/curated/weekly_market_panel.parquet"],
        "tables_or_sheets": ["weekly_market_panel"],
        "fields": ["week_start", "market", "dataset_split", "days_in_week", "min_date", "max_date", "is_complete_week"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["KEY-003", "TEMP-001"],
      "procedure": [
        "Test uniqueness at the claimed panel key.",
        "Enumerate weeks with fewer or more than seven dates and weeks represented in multiple splits.",
        "Confirm min_date, max_date, days_in_week, and is_complete_week agree."
      ],
      "suggested_commands": ["Query duplicate panel keys and DATEDIFF between min_date and max_date."],
      "assertions": ["Each panel key is unique.", "Complete-week flags require exactly seven consecutive dates within one split."],
      "reconciliation": {
        "source_measure": "distinct contributing guest dates",
        "target_measure": "days_in_week",
        "grain": "week_start/market/dataset_split",
        "tolerance": "exact"
      },
      "evidence_required": ["Duplicate count", "partial-week inventory", "split-boundary samples"],
      "completion_criteria": ["All incomplete or overlapping weeks are enumerated and correctly flagged."],
      "possible_issue_fingerprints": ["panel:duplicate-week-market:<key>", "panel:false-complete-week:<key>", "panel:split-boundary-crossing:<week>"],
      "estimated_effort": "small"
    },
    {
      "id": "TEMP-001",
      "domain": "E. Temporal integrity",
      "title": "Map date coverage and continuity by source entity",
      "priority": "P1",
      "objective": "Where are the minimum/maximum dates, missing dates, overlaps, and discontinuities in each source?",
      "risk": "Aggregate coverage can conceal entity-level gaps and partial periods.",
      "scope": {
        "files": ["01a - DCT Dataset/*.xlsx", "lake/curated/*.parquet"],
        "tables_or_sheets": ["Export", "guest_daily", "flight_daily", "flight_monthly", "weekly_market_panel"],
        "fields": ["date", "week_start", "nationality", "departure_country_name", "airline_name", "market"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["RAW-002"],
      "procedure": [
        "Calculate min/max and distinct dates globally and by entity.",
        "Anti-join against expected calendars appropriate to each native grain.",
        "Identify unexpected dates, overlaps, and entity-specific gaps."
      ],
      "suggested_commands": ["Use DuckDB generate_series and anti-joins; do not materialize project tables."],
      "assertions": ["Every gap is distinguishable from an expected inactive entity period.", "Coverage claims specify entity and grain."],
      "reconciliation": {
        "source_measure": "observed entity-date keys",
        "target_measure": "expected calendar keys",
        "grain": "entity/date",
        "tolerance": "0 unexplained gaps; business threshold otherwise requires owner confirmation"
      },
      "evidence_required": ["Coverage table", "gap distributions", "record-level gap samples"],
      "completion_criteria": ["Coverage and gap status are reported for every source entity."],
      "possible_issue_fingerprints": ["time:gap:<dataset>:<entity>:<date>", "time:unexpected-date:<dataset>:<date>", "time:overlap:<dataset>:<key>"],
      "estimated_effort": "large"
    },
    {
      "id": "TEMP-002",
      "domain": "E. Temporal integrity",
      "title": "Validate calendar, ISO-week, and boundary derivations",
      "priority": "P1",
      "objective": "Are leap days, year boundaries, month boundaries, ISO weeks, seasons, holidays, and events derived consistently?",
      "risk": "Calendar mistakes can alter splits, seasonal parameters, and scenario outputs.",
      "scope": {
        "files": ["src/engine/panel.py", "lake/curated/weekly_market_panel.parquet"],
        "tables_or_sheets": ["weekly_market_panel"],
        "fields": ["week_start", "year", "quarter", "month", "iso_week", "season", "is_holiday_week", "is_major_event_week"],
        "date_or_population": "ALL including 2024-02-29 and year boundaries"
      },
      "prerequisites": ["TEMP-001"],
      "procedure": [
        "Independently recompute calendar fields using ISO-8601 rules.",
        "Inspect leap day, week 1, week 52/53, month-spanning weeks, and configured event dates.",
        "Check whether representative_month has a documented rule."
      ],
      "suggested_commands": ["Compute ISO calendar fields independently in DuckDB and compare column by column."],
      "assertions": ["Calendar columns match independently derived values.", "Season and event rules are documented and deterministic."],
      "reconciliation": {
        "source_measure": "week_start",
        "target_measure": "derived calendar fields",
        "grain": "week_start",
        "tolerance": "exact"
      },
      "evidence_required": ["Mismatch counts", "boundary samples", "rule citations"],
      "completion_criteria": ["All calendar mismatches and ambiguous business rules are reported."],
      "possible_issue_fingerprints": ["calendar:iso-week-mismatch:<week>", "calendar:season-mismatch:<week>", "calendar:event-rule-unsupported:<week>"],
      "estimated_effort": "medium"
    },
    {
      "id": "TEMP-003",
      "domain": "E. Temporal integrity",
      "title": "Validate train, holdout, test, and embargo chronology",
      "priority": "P0",
      "objective": "Are all split windows adjacent or intentionally separated, non-overlapping, and reproducible?",
      "risk": "Overlap or mislabeled dates invalidates performance claims.",
      "scope": {
        "files": ["src/engine/panel.py", "scripts/train_models.py", "scripts/evaluate_models.py", "lake/curated/weekly_market_panel.parquet", "lake/curated/evaluation_results.json"],
        "tables_or_sheets": ["weekly_market_panel"],
        "fields": ["date", "week_start", "dataset_split", "target_available"],
        "date_or_population": "2022 through 2026"
      },
      "prerequisites": ["KEY-004", "TEMP-002"],
      "procedure": [
        "Derive exact row and week membership for training, calibration, holdout, and competition test.",
        "Check overlap, adjacency, embargo, and complete-period rules.",
        "Compare code comments, artifact metadata, and actual membership."
      ],
      "suggested_commands": ["Query distinct week_start and dataset_split; inspect all cutoff comparisons in scripts."],
      "assertions": ["No evaluation observation is used in fitting unless explicitly part of a valid rolling design.", "Reported start/end dates match actual week_start values."],
      "reconciliation": {
        "source_measure": "actual split membership",
        "target_measure": "reported split counts and ranges",
        "grain": "week_start/market",
        "tolerance": "exact"
      },
      "evidence_required": ["Membership extract", "overlap counts", "cutoff citations", "count/range comparison"],
      "completion_criteria": ["Every observation has one documented evaluation role."],
      "possible_issue_fingerprints": ["split:overlap:<key>", "split:mislabeled-window:<artifact>", "split:partial-period:<week>"],
      "estimated_effort": "medium"
    },
    {
      "id": "TEMP-004",
      "domain": "E. Temporal integrity",
      "title": "Detect future information in historical features",
      "priority": "P0",
      "objective": "Do lags, rolling values, priors, events, or aggregates use observations later than each row's decision date?",
      "risk": "Future-derived features create temporal leakage even when split labels look correct.",
      "scope": {
        "files": ["src/engine/*.py", "scripts/train_models.py", "scripts/evaluate_models.py"],
        "tables_or_sheets": ["weekly_market_panel", "model inputs"],
        "fields": ["all derived features and fitted parameters"],
        "date_or_population": "Every training and evaluation cutoff"
      },
      "prerequisites": ["TEMP-003", "LIN-002"],
      "procedure": [
        "Inventory each feature's lookback and fit window.",
        "Recompute representative rows using only data available through the prior decision date.",
        "Compare with stored or runtime feature values."
      ],
      "suggested_commands": ["rg -n 'lag|shift|rolling|expanding|groupby|mean|median|fit|cutoff|max_date' engine scripts"],
      "assertions": ["Every feature is point-in-time correct.", "Known-future calendar fields are separated from realized operational fields."],
      "reconciliation": {
        "source_measure": "point-in-time recomputed feature",
        "target_measure": "pipeline feature",
        "grain": "observation/feature",
        "tolerance": "exact for discrete features; 1e-12 for deterministic numeric features"
      },
      "evidence_required": ["Feature availability matrix", "recomputed samples", "violating rows"],
      "completion_criteria": ["Every model feature has a decision-time verdict."],
      "possible_issue_fingerprints": ["leakage:future-feature:<feature>:<cutoff>", "leakage:global-aggregate:<feature>", "leakage:cross-boundary-lag:<key>"],
      "estimated_effort": "large"
    },
    {
      "id": "MISS-001",
      "domain": "F. Missingness and status semantics",
      "title": "Profile cell and missing-row patterns",
      "priority": "P1",
      "objective": "What values and entity-date rows are missing by source, field, market, period, and split?",
      "risk": "Overall null rates can hide systematic population loss.",
      "scope": {
        "files": ["01a - DCT Dataset/*.xlsx", "lake/curated/*.parquet"],
        "tables_or_sheets": ["ALL"],
        "fields": ["ALL"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["RAW-002", "TEMP-001"],
      "procedure": [
        "Compute null, blank, NaN, infinity, and placeholder counts by field and split.",
        "Construct expected entity-date grids and identify absent rows.",
        "Report rates by market, month, and train/test role."
      ],
      "suggested_commands": ["Use read-only SQL GROUP BY summaries and calendar-grid anti-joins."],
      "assertions": ["Cell missingness and missing rows are reported separately.", "Missingness patterns are visible at segment and period level."],
      "reconciliation": {
        "source_measure": "expected entity-date cells",
        "target_measure": "observed, null, status-coded, and absent cells",
        "grain": "dataset/entity/date/field",
        "tolerance": "exact partition"
      },
      "evidence_required": ["Null-rate tables", "missing-row grids", "record samples"],
      "completion_criteria": ["All missing cells and expected-row absences are counted and partitioned."],
      "possible_issue_fingerprints": ["missing:cell:<dataset>:<field>:<segment>", "missing:row:<dataset>:<entity>:<date>", "missing:systematic:<split>:<field>"],
      "estimated_effort": "large"
    },
    {
      "id": "MISS-002",
      "domain": "F. Missingness and status semantics",
      "title": "Validate zero, absent, suppressed, unavailable, and not-applicable semantics",
      "priority": "P0",
      "objective": "Are materially different status states preserved rather than collapsed?",
      "risk": "Treating unavailable or suppressed observations as zero biases totals and training targets.",
      "scope": {
        "files": ["Data_Dictionary.pdf", "scripts/build_lake.py", "lake/curated/guest_daily.parquet", "lake/manifest.json"],
        "tables_or_sheets": ["guest_daily"],
        "fields": ["is_source_present", "target_available", "is_suppressed_arrival", "is_suppressed_same_day", "guests", "new_arrivals", "same_day_guests"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["RAW-003", "MISS-001"],
      "procedure": [
        "Enumerate every raw marker including blanks, asterisks, strings, zeroes, and nulls.",
        "Trace each marker through parsing and curated flags.",
        "Verify aggregates retain enough information to identify partial inputs."
      ],
      "suggested_commands": ["Query cross-tabs of raw marker state versus curated flags and numeric values."],
      "assertions": ["No status state is silently converted to an indistinguishable genuine zero.", "Suppression flags match source markers exactly."],
      "reconciliation": {
        "source_measure": "raw status-marker counts",
        "target_measure": "curated status-flag counts",
        "grain": "source row/field",
        "tolerance": "exact"
      },
      "evidence_required": ["Status mapping table", "marker counts", "mismatch rows"],
      "completion_criteria": ["Every observed source status has a documented curated representation."],
      "possible_issue_fingerprints": ["status:suppressed-as-zero:<field>", "status:absent-as-present:<key>", "status:unavailable-collapsed:<field>"],
      "estimated_effort": "medium"
    },
    {
      "id": "MISS-003",
      "domain": "F. Missingness and status semantics",
      "title": "Audit imputation, null propagation, and split drift",
      "priority": "P1",
      "objective": "How are missing values imputed or propagated, and were imputation statistics fitted without holdout data?",
      "risk": "Leaky imputation and partial aggregates can distort model inputs and performance.",
      "scope": {
        "files": ["scripts/*.py", "src/engine/*.py", "lake/curated/weekly_market_panel.parquet"],
        "tables_or_sheets": ["weekly_market_panel", "model inputs"],
        "fields": ["all nullable inputs", "is_complete_guest_inputs", "missing_arrival_records"],
        "date_or_population": "train versus holdout versus competition test"
      },
      "prerequisites": ["MISS-001", "MISS-002", "TEMP-003"],
      "procedure": [
        "Locate fill, coalesce, fallback, and row-filtering logic.",
        "Identify fit windows for every learned imputation value.",
        "Compare missingness distributions across splits and verify partial sums are flagged."
      ],
      "suggested_commands": ["rg -n 'fillna|coalesce|dropna|is_complete|missing|median|mean|default' scripts engine"],
      "assertions": ["Imputation uses training-only information.", "Partial aggregates are not presented as complete.", "Missingness drift is quantified."],
      "reconciliation": {
        "source_measure": "nullable input rows",
        "target_measure": "imputed, excluded, or propagated rows",
        "grain": "row/field",
        "tolerance": "exact partition"
      },
      "evidence_required": ["Imputation lineage", "fit-window citations", "split missingness comparison", "partial-aggregate samples"],
      "completion_criteria": ["Every nullable model input has an explicit handling and leakage verdict."],
      "possible_issue_fingerprints": ["imputation:holdout-fitted:<field>", "aggregate:partial-presented-complete:<key>", "missingness:split-drift:<field>"],
      "estimated_effort": "medium"
    },
    {
      "id": "NUM-001",
      "domain": "G. Numeric validity and physical constraints",
      "title": "Test non-negativity, integrality, and finite values",
      "priority": "P1",
      "objective": "Do count, capacity, frequency, demand, and monetary-free operational fields satisfy basic numeric domains?",
      "risk": "Invalid values can propagate into ratios, calibration, and scenarios.",
      "scope": {
        "files": ["01a - DCT Dataset/*.xlsx", "lake/curated/*.parquet"],
        "tables_or_sheets": ["ALL"],
        "fields": ["all numeric fields"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["SCH-002"],
      "procedure": [
        "Test finite values, negatives, fractional count fields, and unsafe magnitudes.",
        "Separate raw anomalies from introduced curated anomalies.",
        "Report distributions before choosing any business threshold."
      ],
      "suggested_commands": ["Run min, max, quantiles, nonfinite counts, and x<>floor(x) checks by field."],
      "assertions": ["Physical counts and capacities are non-negative integers unless the contract says otherwise.", "All modelling inputs are finite."],
      "reconciliation": {
        "source_measure": "numeric rows",
        "target_measure": "valid plus enumerated invalid rows",
        "grain": "dataset/row/field",
        "tolerance": "0 invalid values for hard physical constraints"
      },
      "evidence_required": ["Constraint summary", "exception rows", "raw-versus-curated comparison"],
      "completion_criteria": ["Every numeric field has a tested domain and exception count."],
      "possible_issue_fingerprints": ["numeric:negative:<field>:<key>", "numeric:fractional-count:<field>:<key>", "numeric:nonfinite:<field>:<key>"],
      "estimated_effort": "medium"
    },
    {
      "id": "NUM-002",
      "domain": "G. Numeric validity and physical constraints",
      "title": "Reproduce aviation component identities",
      "priority": "P0",
      "objective": "Do seats, passengers, P2P, transfer, transit, class components, and load factor reconcile?",
      "risk": "Failure invalidates the central aviation conversion chain.",
      "scope": {
        "files": ["01a - DCT Dataset/flight_data.xlsx", "lake/curated/flight_daily.parquet", "lake/curated/flight_monthly.parquet"],
        "tables_or_sheets": ["flight_all", "flight_daily", "flight_monthly"],
        "fields": ["total_pax", "total_pax_excluding_infant", "total_p2p", "total_transfer", "total_transit", "total_seats", "load_factor", "class-level counts"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["NUM-001"],
      "procedure": [
        "Test Total PAX = Total P2P + Total Transfer + Total Transit where contractually applicable.",
        "Test class-level components against totals and load_factor against the documented denominator.",
        "Report both aggregate discrepancy and every failing record."
      ],
      "suggested_commands": ["Use read-only SQL expressions for each identity and absolute/relative error."],
      "assertions": ["Passenger identities hold at native row grain.", "Load-factor computation uses the intended passenger measure and seats."],
      "reconciliation": {
        "source_measure": "reported totals",
        "target_measure": "recomputed component totals and ratios",
        "grain": "native flight row",
        "tolerance": "integer identities exact; load-factor absolute error <=1e-12 unless documented rounding applies"
      },
      "evidence_required": ["Mismatch counts", "maximum error", "record-level exceptions", "formula citations"],
      "completion_criteria": ["Every aviation identity has an independently reproduced result."],
      "possible_issue_fingerprints": ["identity:pax-components:<key>", "identity:class-components:<key>", "identity:load-factor:<key>"],
      "estimated_effort": "medium"
    },
    {
      "id": "NUM-003",
      "domain": "G. Numeric validity and physical constraints",
      "title": "Validate guest-stock and arrival relationships",
      "priority": "P1",
      "objective": "Are Guests, New Arrivals, Same-Day Guests, and implied length of stay physically and semantically coherent?",
      "risk": "A misunderstood target or denominator invalidates demand interpretation.",
      "scope": {
        "files": ["Data_Dictionary.pdf", "01a - DCT Dataset/data *.xlsx", "lake/curated/guest_daily.parquet", "lake/curated/weekly_market_panel.parquet"],
        "tables_or_sheets": ["guest_daily", "weekly_market_panel"],
        "fields": ["guests", "new_arrivals", "same_day_guests", "implied_los"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["RAW-003", "MISS-002", "NUM-001"],
      "procedure": [
        "Confirm the PDF meaning of each guest field.",
        "Test only identities and inequalities justified by that meaning.",
        "Profile implied_los by market and season, including zero denominators and extreme values."
      ],
      "suggested_commands": ["Compute ratios and conditional violations at daily and weekly grain."],
      "assertions": ["No unsupported identity is assumed between stock and flow fields.", "Every impossible combination is enumerated."],
      "reconciliation": {
        "source_measure": "weekly guests and new arrivals",
        "target_measure": "reported implied_los",
        "grain": "week_start/market",
        "tolerance": "1e-12 where denominator is positive; null otherwise"
      },
      "evidence_required": ["Definition citations", "distribution tables", "exception samples"],
      "completion_criteria": ["Relationships are classified as proven, unsupported, or violated."],
      "possible_issue_fingerprints": ["guest:impossible-combination:<key>", "guest:los-denominator:<key>", "guest:target-semantic-ambiguity:<field>"],
      "estimated_effort": "medium"
    },
    {
      "id": "NUM-004",
      "domain": "G. Numeric validity and physical constraints",
      "title": "Audit outliers and clipping behavior",
      "priority": "P1",
      "objective": "Which source values are extreme, and are raw and modelling versions both retained when clipping occurs?",
      "risk": "Clipping can conceal operational anomalies and bias model parameters.",
      "scope": {
        "files": ["scripts/build_lake.py", "src/engine/panel.py", "src/engine/structural.py", "lake/curated/*.parquet"],
        "tables_or_sheets": ["flight_daily", "weekly_market_panel"],
        "fields": ["load_factor_raw", "load_factor", "p2p_share", "implied_los", "effective_response_multiplier", "all volume fields"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["NUM-001", "NUM-002", "NUM-003"],
      "procedure": [
        "Profile quantiles, spikes, discontinuities, and clustered outliers by entity and time.",
        "Locate every clip, cap, floor, winsorization, and max/min operation.",
        "Verify raw values and flags remain traceable."
      ],
      "suggested_commands": ["rg -n 'clip|maximum|minimum|max\\(|min\\(|winsor|outlier' scripts engine"],
      "assertions": ["No source anomaly is silently overwritten.", "Every model-time bound has a documented physical or statistical rationale."],
      "reconciliation": {
        "source_measure": "raw values",
        "target_measure": "model values plus retained raw values and flags",
        "grain": "row/field",
        "tolerance": "exact traceability"
      },
      "evidence_required": ["Outlier distributions", "code citations", "before/after values", "flag coverage"],
      "completion_criteria": ["Every value-changing bound is inventoried and evidenced."],
      "possible_issue_fingerprints": ["numeric:silent-clipping:<field>", "numeric:outlier-unflagged:<field>:<key>", "numeric:unsupported-cap:<field>"],
      "estimated_effort": "medium"
    },
    {
      "id": "CAT-001",
      "domain": "H. Categorical and entity quality",
      "title": "Profile exact and normalized category values",
      "priority": "P1",
      "objective": "Which categorical values differ only by whitespace, case, punctuation, Unicode, spelling, or aliases?",
      "risk": "Label variants fragment markets and break joins.",
      "scope": {
        "files": ["01a - DCT Dataset/*.xlsx", "lake/curated/*.parquet"],
        "tables_or_sheets": ["ALL"],
        "fields": ["Nationality", "Residence (groups)", "Departure Country Name", "Departure City", "Arrival City", "Airline Name", "Destination", "market", "season", "archetype"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["RAW-002"],
      "procedure": [
        "Compute exact cardinality and multiple normalized forms.",
        "Identify collisions where distinct raw labels normalize identically.",
        "Retain raw labels, code points, counts, and periods."
      ],
      "suggested_commands": ["Profile TRIM, UPPER, Unicode-normalized, punctuation-stripped values without modifying data."],
      "assertions": ["Every normalization collision is reviewed.", "Raw labels remain traceable after mapping."],
      "reconciliation": {
        "source_measure": "exact categories",
        "target_measure": "normalized categories plus collision mapping",
        "grain": "dataset/field/value",
        "tolerance": "exact accounting"
      },
      "evidence_required": ["Cardinality table", "normalization collision list", "frequency and date ranges"],
      "completion_criteria": ["All category variants and collisions are enumerated."],
      "possible_issue_fingerprints": ["category:variant:<field>:<normalized>", "category:normalization-collision:<field>:<normalized>", "category:encoding:<field>:<value>"],
      "estimated_effort": "medium"
    },
    {
      "id": "CAT-002",
      "domain": "H. Categorical and entity quality",
      "title": "Validate market and regional mapping completeness",
      "priority": "P0",
      "objective": "Do nationality and departure-country values map deterministically to top-15, regional clusters, OTHER, or DOMESTIC?",
      "risk": "Unmapped or multiply mapped categories alter the central market bridge.",
      "scope": {
        "files": ["src/engine/archetypes.py", "src/engine/panel.py", "01a - DCT Dataset/*.xlsx"],
        "tables_or_sheets": ["guest_daily", "flight_daily", "weekly_market_panel"],
        "fields": ["nationality", "departure_country_name", "market", "TOP_15_INTERNATIONAL_MARKETS", "REGIONAL_CLUSTERS"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["CAT-001"],
      "procedure": [
        "Apply mappings independently to every observed source label.",
        "Detect unmapped values, multiple memberships, collisions, and mismatched guest/flight outcomes.",
        "Reconcile mapped control totals to source totals."
      ],
      "suggested_commands": ["Extract mapping constants and compare membership sets; independently reproduce CASE results."],
      "assertions": ["Every category maps exactly once.", "Guest and flight labels use the same documented normalization without asserting entity equivalence."],
      "reconciliation": {
        "source_measure": "source rows and totals by category",
        "target_measure": "mapped rows and totals by market",
        "grain": "source category",
        "tolerance": "exact"
      },
      "evidence_required": ["Mapping matrix", "unmapped and collision lists", "control totals"],
      "completion_criteria": ["Every observed source label has one deterministic mapping result."],
      "possible_issue_fingerprints": ["mapping:unmapped:<field>:<value>", "mapping:multiple-clusters:<value>", "mapping:guest-flight-inconsistent:<value>"],
      "estimated_effort": "medium"
    },
    {
      "id": "CAT-003",
      "domain": "H. Categorical and entity quality",
      "title": "Audit category drift and archetype evidence",
      "priority": "P2",
      "objective": "Which categories appear or disappear by period/split, and what evidence supports archetype assignments and fallbacks?",
      "risk": "New categories and unsupported classifications create fragile cold-start behavior.",
      "scope": {
        "files": ["src/engine/archetypes.py", "lake/curated/weekly_market_panel.parquet", "lake/curated/structural_calibration.json"],
        "tables_or_sheets": ["weekly_market_panel"],
        "fields": ["market", "archetype", "dataset_split", "COUNTRY_TO_REGION_MAP"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["CAT-002", "TEMP-001"],
      "procedure": [
        "Compare category sets and volumes across years and splits.",
        "Trace each archetype and fallback to empirical or documented evidence.",
        "Identify unsupported, disappearing, and new categories."
      ],
      "suggested_commands": ["Query first/last appearance and counts by market; inspect mapping comments and documentation."],
      "assertions": ["Archetypes are reproducible and not presented as observed facts without evidence.", "Unseen categories have visible fallbacks."],
      "reconciliation": {
        "source_measure": "observed categories",
        "target_measure": "archetype and fallback assignments",
        "grain": "category",
        "tolerance": "exact coverage; evidentiary thresholds require owner confirmation"
      },
      "evidence_required": ["Category-drift table", "assignment citations", "unsupported mapping list"],
      "completion_criteria": ["Every current and unseen category path is documented and classified."],
      "possible_issue_fingerprints": ["category:new-in-evaluation:<value>", "archetype:unsupported:<market>", "fallback:invisible:<market>"],
      "estimated_effort": "medium"
    },
    {
      "id": "BRG-001",
      "domain": "I. Origin-to-nationality bridge",
      "title": "Prove the implemented origin-to-nationality operation",
      "priority": "P0",
      "objective": "Does the implementation equate departure country with guest nationality, allocate across entities, or use another bridge?",
      "risk": "False entity equivalence can invalidate market-level demand estimates.",
      "scope": {
        "files": ["src/engine/panel.py", "src/engine/structural.py", "scripts/evaluate_models.py"],
        "tables_or_sheets": ["flight_daily", "guest_daily", "weekly_market_panel"],
        "fields": ["departure_country_name", "nationality", "market", "effective_response_multiplier"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["CAT-002", "KEY-003"],
      "procedure": [
        "Trace both source entities through mapping, aggregation, and joining.",
        "Write the exact implemented mathematical relationship.",
        "Identify where same-label matching is assumed and where no individual linkage exists."
      ],
      "suggested_commands": ["Inspect panel SQL and independently reproduce one market-week mapping."],
      "assertions": ["The exact bridge is evidenced in code and data.", "Same labels are not treated as proof of passenger nationality."],
      "reconciliation": {
        "source_measure": "flight-origin and guest-nationality mapped totals",
        "target_measure": "panel market totals",
        "grain": "week_start/market/source-domain",
        "tolerance": "exact"
      },
      "evidence_required": ["Code citations", "equation", "worked market-week example", "unmatched categories"],
      "completion_criteria": ["The bridge is fully specified without inventing unobserved linkage."],
      "possible_issue_fingerprints": ["bridge:origin-equals-nationality:<stage>", "bridge:unobserved-linkage-claimed", "bridge:mapping-total-loss:<market>"],
      "estimated_effort": "large"
    },
    {
      "id": "BRG-002",
      "domain": "I. Origin-to-nationality bridge",
      "title": "Assess bridge coverage and identifiability",
      "priority": "P0",
      "objective": "Are the allocation or effective multiplier parameters identifiable from available aggregate data?",
      "risk": "Unidentifiable components may be falsely presented as separately measured behavior.",
      "scope": {
        "files": ["lake/curated/weekly_market_panel.parquet", "lake/curated/structural_calibration.json", "src/engine/structural.py"],
        "tables_or_sheets": ["weekly_market_panel"],
        "fields": ["p2p", "new_arrivals", "effective_response_multiplier", "market", "season", "historical_weeks"],
        "date_or_population": "training rows"
      },
      "prerequisites": ["BRG-001", "TEMP-003"],
      "procedure": [
        "Document observable equations, unknowns, rank, and sample size.",
        "Count market-season cells and assess denominator support and parameter stability.",
        "Determine whether nationality allocation, visitor purpose, hotel capture, and stay behavior can be separately identified."
      ],
      "suggested_commands": ["Compute design rank, market-season counts, denominator totals, and bootstrap parameter variation."],
      "assertions": ["Only identifiable quantities are described as measured.", "Effective multipliers are labeled as composite predictive parameters where appropriate."],
      "reconciliation": {
        "source_measure": "observable market-week equations",
        "target_measure": "estimated bridge parameters",
        "grain": "market/season",
        "tolerance": "No numerical tolerance; rank and identifiability verdict required"
      },
      "evidence_required": ["Equation/rank analysis", "sample counts", "parameter distribution", "claim comparison"],
      "completion_criteria": ["Each bridge component is classified identifiable, regularized assumption, or unidentifiable."],
      "possible_issue_fingerprints": ["bridge:unidentifiable-component:<name>", "bridge:composite-mislabeled:<claim>", "bridge:sparse-parameter:<market>:<season>"],
      "estimated_effort": "large"
    },
    {
      "id": "BRG-003",
      "domain": "I. Origin-to-nationality bridge",
      "title": "Validate bridge fallback and seasonality",
      "priority": "P1",
      "objective": "Are unsupported markets and missing market-season cells handled visibly and consistently?",
      "risk": "Silent defaults can generate precise-looking estimates without local evidence.",
      "scope": {
        "files": ["src/engine/archetypes.py", "src/engine/structural.py", "lake/curated/structural_calibration.json"],
        "tables_or_sheets": ["structural calibration"],
        "fields": ["market", "season", "historical_weeks", "is_cold_start", "default_multiplier", "effective_response_multiplier"],
        "date_or_population": "ALL markets and four seasons"
      },
      "prerequisites": ["BRG-002", "CAT-003"],
      "procedure": [
        "Enumerate all direct, missing-season, regional, legacy OTHER, and generic fallback paths.",
        "Compare fallback values with supported distributions.",
        "Verify API/UI expose is_cold_start and the basis of fallback."
      ],
      "suggested_commands": ["Call get_or_create_params read-only for supported, partial, and unknown markets."],
      "assertions": ["Fallback selection is deterministic and visible.", "Missing seasons do not masquerade as calibrated local estimates."],
      "reconciliation": {
        "source_measure": "requested market-season combinations",
        "target_measure": "resolved parameter sources",
        "grain": "market/season",
        "tolerance": "exact route to one source"
      },
      "evidence_required": ["Fallback decision table", "parameter comparisons", "API samples"],
      "completion_criteria": ["Every requested combination has an explicit parameter provenance."],
      "possible_issue_fingerprints": ["bridge:silent-fallback:<market>:<season>", "bridge:legacy-other-mismatch", "bridge:cold-start-mislabeled:<market>"],
      "estimated_effort": "medium"
    },
    {
      "id": "BRG-004",
      "domain": "I. Origin-to-nationality bridge",
      "title": "Measure sensitivity to defensible bridge alternatives",
      "priority": "P1",
      "objective": "How materially do results change under diagonal, regional-pooling, and bounded alternative bridge assumptions?",
      "risk": "Central conclusions may depend more on the bridge assumption than on aviation changes.",
      "scope": {
        "files": ["lake/curated/weekly_market_panel.parquet", "src/engine/structural.py"],
        "tables_or_sheets": ["weekly_market_panel"],
        "fields": ["market", "season", "p2p", "new_arrivals", "guests"],
        "date_or_population": "Representative high-volume, sparse, and hub-mediated markets"
      },
      "prerequisites": ["BRG-002", "BRG-003"],
      "procedure": [
        "Define a finite set of alternatives using only observable aggregates and documented bounds.",
        "Recompute parameters and scenario outcomes without modifying artifacts.",
        "Report relative and absolute result ranges by market."
      ],
      "suggested_commands": ["Use a temporary in-memory DuckDB or local dataframe; do not save model artifacts."],
      "assertions": ["Sensitivity is reported rather than selecting an alternative as truth.", "Material dependence on bridge choice is visible."],
      "reconciliation": {
        "source_measure": "current bridge scenario result",
        "target_measure": "alternative bridge scenario results",
        "grain": "market/season/scenario",
        "tolerance": "Report full distribution; materiality threshold requires owner confirmation"
      },
      "evidence_required": ["Alternative definitions", "result table", "largest changes", "assumption labels"],
      "completion_criteria": ["At least three defensible assumptions are compared for each selected market type."],
      "possible_issue_fingerprints": ["bridge:sensitivity-high:<market>", "bridge:assumption-dominates:<scenario>", "bridge:uncertainty-omitted"],
      "estimated_effort": "large"
    },
    {
      "id": "AGG-001",
      "domain": "J. Aggregation correctness",
      "title": "Inventory and validate every aggregation operator",
      "priority": "P1",
      "objective": "Is each SUM, AVG, weighted mean, MIN, MAX, first/last, count, and deduplication appropriate to native grain?",
      "risk": "A single wrong operator can distort all downstream values.",
      "scope": {
        "files": ["scripts/build_lake.py", "src/engine/panel.py", "scripts/train_models.py", "scripts/evaluate_models.py", "sql/*.sql"],
        "tables_or_sheets": ["ALL transformed objects"],
        "fields": ["ALL aggregated fields"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["KEY-001", "KEY-002"],
      "procedure": [
        "Extract each aggregation expression with input and output grain.",
        "State the mathematically correct operator and denominator from the source contract.",
        "Independently recompute a representative period and all edge-case groups."
      ],
      "suggested_commands": ["rg -n 'SUM\\(|AVG\\(|MIN\\(|MAX\\(|groupby|agg\\(|mean\\(|sum\\(|first\\(|last\\(' scripts engine sql"],
      "assertions": ["Every aggregation has a documented grain and rationale.", "Frequency, ratios, and stock measures are not summed or averaged incorrectly."],
      "reconciliation": {
        "source_measure": "native-grain inputs",
        "target_measure": "published aggregates",
        "grain": "each transformation's target key",
        "tolerance": "exact for sums/counts; 1e-12 for deterministic ratios"
      },
      "evidence_required": ["Aggregation catalog", "formula citations", "recomputed samples", "exceptions"],
      "completion_criteria": ["Every aggregation expression has an explicit verdict."],
      "possible_issue_fingerprints": ["aggregation:wrong-operator:<field>:<stage>", "aggregation:wrong-denominator:<field>", "aggregation:invalid-grain:<stage>"],
      "estimated_effort": "large"
    },
    {
      "id": "AGG-002",
      "domain": "J. Aggregation correctness",
      "title": "Validate ratio denominators and weighted means",
      "priority": "P0",
      "objective": "Are load factor, P2P share, implied LOS, effective multiplier, bias, and WMAPE computed from correct totals and denominators?",
      "risk": "Averaging row ratios instead of dividing totals can materially change parameters and metrics.",
      "scope": {
        "files": ["src/engine/panel.py", "src/engine/structural.py", "scripts/evaluate_models.py"],
        "tables_or_sheets": ["weekly_market_panel", "evaluation results"],
        "fields": ["load_factor", "p2p_share", "implied_los", "effective_response_multiplier", "bias", "wmape"],
        "date_or_population": "ALL relevant groups"
      },
      "prerequisites": ["AGG-001", "NUM-002", "NUM-003"],
      "procedure": [
        "Write the numerator and denominator for every ratio.",
        "Compare ratio-of-sums with mean-of-ratios and identify the implemented form.",
        "Evaluate zero-denominator and null behavior."
      ],
      "suggested_commands": ["Independently compute both formulations by market, season, and split."],
      "assertions": ["Volume ratios use ratio-of-compatible totals unless another estimator is justified.", "Zero denominators never silently yield misleading zero performance."],
      "reconciliation": {
        "source_measure": "independently recomputed ratios",
        "target_measure": "stored or reported ratios",
        "grain": "market/season/split",
        "tolerance": "1e-12"
      },
      "evidence_required": ["Formula table", "comparison distribution", "zero-denominator cases"],
      "completion_criteria": ["All material ratios and weighted means are reproduced."],
      "possible_issue_fingerprints": ["ratio:mean-of-ratios:<field>", "ratio:wrong-denominator:<field>", "ratio:zero-denominator:<field>:<group>"],
      "estimated_effort": "medium"
    },
    {
      "id": "AGG-003",
      "domain": "J. Aggregation correctness",
      "title": "Reconcile OTHER and regional aggregation",
      "priority": "P1",
      "objective": "Do OTHER INTERNATIONAL, OTHER_INTERNATIONAL, and five regional clusters preserve source populations and totals consistently?",
      "risk": "Legacy and current labels can split or double-count the same population.",
      "scope": {
        "files": ["src/engine/archetypes.py", "src/engine/panel.py", "lake/curated/weekly_market_panel.parquet", "lake/curated/*.json"],
        "tables_or_sheets": ["weekly_market_panel"],
        "fields": ["market", "nationality", "departure_country_name", "guests", "seats", "pax", "p2p"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["CAT-002", "AGG-001"],
      "procedure": [
        "Identify every legacy and current pooled label in code and artifacts.",
        "Recompute pooled totals directly from source members.",
        "Detect overlap, omission, and consumer incompatibility."
      ],
      "suggested_commands": ["Query market label sets and sum mapped source members by week and split."],
      "assertions": ["Each source category contributes to exactly one pooled group.", "Artifacts and runtime consumers use compatible pooled labels."],
      "reconciliation": {
        "source_measure": "member-category totals",
        "target_measure": "pooled market totals",
        "grain": "week_start/split/measure",
        "tolerance": "exact"
      },
      "evidence_required": ["Membership sets", "weekly total comparisons", "label-consumer matrix"],
      "completion_criteria": ["Every pooled label has exact membership and total reconciliation."],
      "possible_issue_fingerprints": ["other:double-count:<category>", "other:omitted:<category>", "other:legacy-label-incompatible:<artifact>"],
      "estimated_effort": "medium"
    },
    {
      "id": "AGG-004",
      "domain": "J. Aggregation correctness",
      "title": "Test rounding order and segment dominance",
      "priority": "P2",
      "objective": "Do rounding, high-volume segments, or Simpson's paradox change reported aggregate conclusions?",
      "risk": "Combined metrics may conceal weak international or sparse-market performance.",
      "scope": {
        "files": ["scripts/evaluate_models.py", "lake/curated/evaluation_results.json", "README.md", "docs/*.md"],
        "tables_or_sheets": ["evaluation populations"],
        "fields": ["actual", "prediction", "wmape", "bias", "mae", "rmse", "market", "is_domestic"],
        "date_or_population": "holdout"
      },
      "prerequisites": ["AGG-002", "MET-002"],
      "procedure": [
        "Recompute metrics with full precision and with documented display rounding.",
        "Compare micro, macro, domestic, international, volume-tier, and market-weighted results.",
        "Identify sign reversals or conclusions driven by dominant segments."
      ],
      "suggested_commands": ["Recompute metrics from retained evaluation rows in a temporary process."],
      "assertions": ["Rounding occurs only after aggregation.", "Combined metrics are accompanied by disaggregated evidence."],
      "reconciliation": {
        "source_measure": "full-precision segment metrics",
        "target_measure": "reported aggregate and rounded metrics",
        "grain": "metric/population",
        "tolerance": "display rounding to stated precision only"
      },
      "evidence_required": ["Metric comparison table", "segment weights", "reversal analysis"],
      "completion_criteria": ["All dominance and rounding effects are quantified."],
      "possible_issue_fingerprints": ["metric:round-before-aggregate:<metric>", "metric:domestic-masks-international", "metric:simpsons-paradox:<metric>"],
      "estimated_effort": "medium"
    },
    {
      "id": "REC-001",
      "domain": "K. Source-to-target reconciliation",
      "title": "Reconcile Excel rows into DuckDB raw/all objects",
      "priority": "P0",
      "objective": "Does every source row enter the database exactly once with preserved control totals and statuses?",
      "risk": "Loss or multiplication at ingestion contaminates every downstream result.",
      "scope": {
        "files": ["01a - DCT Dataset/*.xlsx", "scripts/build_lake.py", "lake/analytics.duckdb"],
        "tables_or_sheets": ["Export", "guest_daily", "flight_all"],
        "fields": ["all keys, counts, ratios, categories, source_file"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["RAW-002", "SCH-002", "KEY-001", "KEY-002"],
      "procedure": [
        "Independently read sources and compute rows, distinct keys, and additive totals.",
        "Compare with database rows by source_file, period, category, and split.",
        "Extract unmatched and multiply represented source records."
      ],
      "suggested_commands": ["Open DuckDB read-only and join independent source extracts by candidate key."],
      "assertions": ["Every raw source record has one auditable database representation.", "Source totals and statuses are preserved."],
      "reconciliation": {
        "source_measure": "rows, distinct keys, and additive source totals",
        "target_measure": "DuckDB corresponding measures",
        "grain": "source_file/period/category",
        "tolerance": "exact; ratio values within 1e-12"
      },
      "evidence_required": ["Control totals", "unmatched rows", "duplicate matches", "query text"],
      "completion_criteria": ["Aggregate and record-level reconciliation both complete."],
      "possible_issue_fingerprints": ["recon:excel-duckdb:loss:<file>", "recon:excel-duckdb:duplication:<file>", "recon:excel-duckdb:value-change:<field>"],
      "estimated_effort": "large"
    },
    {
      "id": "REC-002",
      "domain": "K. Source-to-target reconciliation",
      "title": "Reconcile raw guests to guest_daily grid",
      "priority": "P0",
      "objective": "Are source-present, grid-absent, labeled, and prediction rows accounted for exactly?",
      "risk": "Incorrect grid expansion changes missingness, targets, and split populations.",
      "scope": {
        "files": ["scripts/build_lake.py", "lake/curated/guest_daily.parquet", "lake/manifest.json"],
        "tables_or_sheets": ["guest_daily", "guest_actuals", "guest_prediction_rows"],
        "fields": ["date", "nationality", "residence_group", "dataset_split", "is_source_present", "target_available", "guests", "new_arrivals", "same_day_guests"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["REC-001", "MISS-002"],
      "procedure": [
        "Partition curated rows by presence and target availability.",
        "Match source-present rows to raw rows and independently generate the expected grid.",
        "Compare row counts and totals by split, market, and month; retain exceptions."
      ],
      "suggested_commands": ["Use in-memory expected grids and anti-joins; verify manifest counts independently."],
      "assertions": ["Grid-only rows are flagged and do not invent target values.", "Source-present values reconcile exactly."],
      "reconciliation": {
        "source_measure": "raw guest rows and expected entity-date grid",
        "target_measure": "guest_daily partitions",
        "grain": "date/residence_group/nationality/dataset_split",
        "tolerance": "exact"
      },
      "evidence_required": ["Partition counts", "control totals", "unmatched keys", "flag/value contradictions"],
      "completion_criteria": ["Every curated guest row is classified as matched source or justified grid row."],
      "possible_issue_fingerprints": ["recon:guest-grid:missing-source:<key>", "recon:guest-grid:invented-value:<key>", "recon:guest-grid:flag-contradiction:<key>"],
      "estimated_effort": "large"
    },
    {
      "id": "REC-003",
      "domain": "K. Source-to-target reconciliation",
      "title": "Reconcile raw flights to daily and monthly Parquet",
      "priority": "P0",
      "objective": "Does the daily/monthly partition preserve every flight row and control total?",
      "risk": "Incorrect grain partitioning or lost rows breaks the aviation baseline.",
      "scope": {
        "files": ["scripts/build_lake.py", "lake/curated/flight_daily.parquet", "lake/curated/flight_monthly.parquet", "lake/manifest.json"],
        "tables_or_sheets": ["flight_all", "flight_daily", "flight_monthly"],
        "fields": ["date", "source_grain", "all additive flight measures", "is_load_factor_outlier"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["REC-001", "KEY-002", "NUM-002"],
      "procedure": [
        "Recompute source-grain classification independently.",
        "Compare row counts, distinct keys, totals, and outlier flags by year and market.",
        "Anti-join source rows against the union of both curated files."
      ],
      "suggested_commands": ["Run read-only union and anti-join queries across DuckDB and Parquet."],
      "assertions": ["Every flight row enters exactly one grain-specific artifact.", "Additive controls reconcile exactly."],
      "reconciliation": {
        "source_measure": "flight_all rows and additive totals",
        "target_measure": "flight_daily union flight_monthly",
        "grain": "year/source_grain/departure_country",
        "tolerance": "exact"
      },
      "evidence_required": ["Partition controls", "unmatched and duplicate rows", "outlier-flag comparison"],
      "completion_criteria": ["Union reconciliation and exception audit both complete."],
      "possible_issue_fingerprints": ["recon:flight-partition:loss:<key>", "recon:flight-partition:double:<key>", "recon:flight-outlier-flag:<key>"],
      "estimated_effort": "medium"
    },
    {
      "id": "REC-004",
      "domain": "K. Source-to-target reconciliation",
      "title": "Reconcile curated daily data to weekly_market_panel",
      "priority": "P0",
      "objective": "Do weekly market totals equal independent daily aggregations without join fan-out?",
      "risk": "The modelling panel is the common input to calibration, evaluation, and simulation.",
      "scope": {
        "files": ["src/engine/panel.py", "lake/analytics.duckdb", "lake/curated/weekly_market_panel.parquet"],
        "tables_or_sheets": ["guest_daily", "flight_daily", "weekly_market_panel"],
        "fields": ["seats", "pax", "p2p", "transfer_pax", "transit_pax", "guests", "new_arrivals", "same_day_guests", "days_in_week"],
        "date_or_population": "2023 onward"
      },
      "prerequisites": ["REC-002", "REC-003", "KEY-003", "AGG-001"],
      "procedure": [
        "Independently map markets and aggregate daily guest and flight domains before joining.",
        "Compare each panel measure by week, market, and split.",
        "Extract all mismatches and trace their contributing daily rows."
      ],
      "suggested_commands": ["Use independent read-only SQL CTEs, avoiding reuse of engine.panel SQL."],
      "assertions": ["Every weekly measure reconciles to daily sources.", "Flight totals are not duplicated across guest markets or split-boundary rows."],
      "reconciliation": {
        "source_measure": "independent daily aggregates",
        "target_measure": "weekly panel measures",
        "grain": "week_start/market/dataset_split",
        "tolerance": "exact for integer-derived totals; absolute error <=1e-9 for doubles"
      },
      "evidence_required": ["Measure-level mismatch counts", "maximum differences", "record-level exception traces"],
      "completion_criteria": ["Every panel measure is reconciled with exceptions retained."],
      "possible_issue_fingerprints": ["recon:daily-weekly:<measure>:<key>", "recon:panel-fanout:<key>", "recon:panel-row-loss:<key>"],
      "estimated_effort": "large"
    },
    {
      "id": "REC-005",
      "domain": "K. Source-to-target reconciliation",
      "title": "Reconcile weekly panel to training and calibration artifacts",
      "priority": "P0",
      "objective": "Can every structural parameter and residual-model training population be regenerated from eligible panel rows?",
      "risk": "Artifact values may be stale, leaky, or generated from a different population.",
      "scope": {
        "files": ["scripts/train_models.py", "src/engine/structural.py", "src/engine/residual.py", "lake/curated/weekly_market_panel.parquet", "lake/curated/structural_calibration.json", "lake/curated/residual_engine.pkl"],
        "tables_or_sheets": ["weekly_market_panel", "model training inputs"],
        "fields": ["all parameter fields, features, residuals, market, season, historical_weeks"],
        "date_or_population": "artifact training cutoff"
      },
      "prerequisites": ["REC-004", "TEMP-003", "LEAK-001"],
      "procedure": [
        "Reconstruct eligible training rows from documented filters.",
        "Recompute structural parameters and residual features independently.",
        "Compare values, population counts, feature order, and cutoff metadata to artifacts."
      ],
      "suggested_commands": ["Run regeneration in memory with save paths disabled; inspect pickle in an isolated process."],
      "assertions": ["Artifacts exactly reflect the documented training population and formulas.", "No excluded or future rows contribute."],
      "reconciliation": {
        "source_measure": "eligible panel rows and independently recomputed parameters",
        "target_measure": "saved artifacts",
        "grain": "market/season/parameter and model feature",
        "tolerance": "1e-12 for deterministic JSON values; exact population and feature sets"
      },
      "evidence_required": ["Population counts", "parameter diffs", "feature metadata", "exception list"],
      "completion_criteria": ["Every saved model component has a reproducible panel lineage."],
      "possible_issue_fingerprints": ["recon:panel-calibration:<market>:<season>:<parameter>", "artifact:stale-training-population", "artifact:feature-mismatch"],
      "estimated_effort": "large"
    },
    {
      "id": "REC-006",
      "domain": "K. Source-to-target reconciliation",
      "title": "Reconcile panel evaluation populations and saved metrics",
      "priority": "P0",
      "objective": "Do actual evaluation rows, predictions, counts, and metrics reproduce evaluation_results.json?",
      "risk": "Non-reproducible headline metrics undermine the central accuracy claim.",
      "scope": {
        "files": ["scripts/evaluate_models.py", "lake/curated/weekly_market_panel.parquet", "lake/curated/evaluation_results.json"],
        "tables_or_sheets": ["evaluation populations"],
        "fields": ["actual", "prediction", "market", "season", "wmape", "bias", "mae", "rmse", "coverage"],
        "date_or_population": "104 training weeks and 30 holdout weeks as claimed"
      },
      "prerequisites": ["REC-005", "MET-002"],
      "procedure": [
        "Recreate population membership and predictions without overwriting artifacts.",
        "Recompute every overall, diagnostic, benchmark, market, season, and coverage value.",
        "Compare counts, ranges, and metrics at full precision."
      ],
      "suggested_commands": ["Run a read-only copy of evaluation logic with artifact writes disabled or redirected to a temporary audit directory."],
      "assertions": ["Every saved metric is reproducible from retained observations.", "Population counts and windows match the artifact."],
      "reconciliation": {
        "source_measure": "recomputed evaluation observations and metrics",
        "target_measure": "evaluation_results.json",
        "grain": "population/segment/metric",
        "tolerance": "counts exact; numeric absolute error <=5e-13 before documented rounding"
      },
      "evidence_required": ["Observation-level extract", "metric diff table", "population exceptions", "command and environment"],
      "completion_criteria": ["Every saved metric has a reproduced or contradicted verdict."],
      "possible_issue_fingerprints": ["recon:evaluation-metric:<population>:<metric>", "recon:evaluation-count:<population>", "evaluation:unretained-predictions"],
      "estimated_effort": "large"
    },
    {
      "id": "REC-007",
      "domain": "K. Source-to-target reconciliation",
      "title": "Reconcile artifacts, simulator, API, and UI values",
      "priority": "P0",
      "objective": "Do identical scenario inputs produce the same parameters, chain values, waterfall, uncertainty, API response, and UI display?",
      "risk": "Cross-layer drift can make the planner see values not supported by the model artifacts.",
      "scope": {
        "files": ["src/engine/*.py", "src/app/server.py", "src/app/static/index.html", "lake/curated/*.json", "lake/curated/residual_engine.pkl"],
        "tables_or_sheets": ["NOT_APPLICABLE"],
        "fields": ["conversion_chain", "waterfall", "hybrid", "uncertainty", "tornado", "coverage_pct"],
        "date_or_population": "Finite scenarios: default UK winter, domestic, cold-start, closure"
      },
      "prerequisites": ["REC-005", "SCEN-001", "SCEN-003"],
      "procedure": [
        "Run each fixed scenario directly through engine APIs and HTTP handler using deterministic inputs.",
        "Capture API JSON and independently evaluate UI formatting and totals.",
        "Compare every numeric field and label across layers."
      ],
      "suggested_commands": ["Use local unit-style handler invocation or localhost server; no external service."],
      "assertions": ["Same inputs yield identical underlying values across engine and API.", "UI displays the intended API fields with only documented formatting."],
      "reconciliation": {
        "source_measure": "engine ScenarioReport",
        "target_measure": "API JSON and UI values",
        "grain": "scenario/output field",
        "tolerance": "exact before UI formatting; display rounding to shown precision"
      },
      "evidence_required": ["Scenario inputs", "engine/API/UI comparison", "field-level mismatches"],
      "completion_criteria": ["All selected scenarios reconcile field by field."],
      "possible_issue_fingerprints": ["recon:engine-api:<field>", "recon:api-ui:<field>", "recon:scenario-label:<field>"],
      "estimated_effort": "large"
    },
    {
      "id": "LIN-001",
      "domain": "L. Transformation and feature lineage",
      "title": "Trace every published field to its source",
      "priority": "P1",
      "objective": "What source, formula, unit, filter, and status semantics produce each API, UI, report, and evaluation field?",
      "risk": "Published fields without lineage cannot be interpreted or independently checked.",
      "scope": {
        "files": ["scripts/*.py", "src/engine/*.py", "src/app/**/*", "docs/*.md", "output/**/*"],
        "tables_or_sheets": ["ALL"],
        "fields": ["all published fields"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["INV-002", "RAW-003"],
      "procedure": [
        "Inventory published field names and labels.",
        "Trace each backward through artifacts, transformations, raw fields, formulas, filters, and unit changes.",
        "Record observed, derived, assumed, imputed, model-estimated, and planner-override status."
      ],
      "suggested_commands": ["rg -n for each API key, UI label, report metric, and artifact field."],
      "assertions": ["Every published field has one complete lineage.", "Evidence class and decision-time availability are explicit."],
      "reconciliation": {
        "source_measure": "published fields",
        "target_measure": "completed lineage records",
        "grain": "field",
        "tolerance": "100% coverage"
      },
      "evidence_required": ["Lineage matrix", "file:line citations", "unit and classification columns"],
      "completion_criteria": ["No published field remains without source and transformation provenance."],
      "possible_issue_fingerprints": ["lineage:missing:<field>", "lineage:unit-change-undocumented:<field>", "lineage:evidence-class-mislabeled:<field>"],
      "estimated_effort": "large"
    },
    {
      "id": "LIN-002",
      "domain": "L. Transformation and feature lineage",
      "title": "Audit model feature construction and fit windows",
      "priority": "P0",
      "objective": "How are calendar, event, seasonal, structural, residual, normalization, and encoding features produced and fitted?",
      "risk": "Feature lineage errors and global fitting create hidden leakage.",
      "scope": {
        "files": ["src/engine/panel.py", "src/engine/residual.py", "scripts/train_models.py", "scripts/evaluate_models.py"],
        "tables_or_sheets": ["weekly_market_panel", "residual model inputs"],
        "fields": ["year", "quarter", "month", "iso_week", "season", "holiday/event flags", "all residual features"],
        "date_or_population": "ALL training and evaluation rows"
      },
      "prerequisites": ["LIN-001", "TEMP-003"],
      "procedure": [
        "Enumerate feature formulas, fit operations, and required source dates.",
        "Record per-feature decision-time availability and fit population.",
        "Check ordering, encoding determinism, and unknown-category handling."
      ],
      "suggested_commands": ["Inspect extract_calendar_features, model fit calls, and preprocessing operations."],
      "assertions": ["All preprocessing is trained on eligible data only.", "Feature order and category handling are deterministic."],
      "reconciliation": {
        "source_measure": "independently recomputed feature vectors",
        "target_measure": "model input vectors",
        "grain": "observation/feature",
        "tolerance": "exact or 1e-12 for numeric transforms"
      },
      "evidence_required": ["Feature catalog", "fit-window matrix", "sample vector comparisons"],
      "completion_criteria": ["Every feature has formula, source date, and fit-window evidence."],
      "possible_issue_fingerprints": ["feature:global-fit:<feature>", "feature:order-nondeterministic", "feature:decision-time-unavailable:<feature>"],
      "estimated_effort": "large"
    },
    {
      "id": "LIN-003",
      "domain": "L. Transformation and feature lineage",
      "title": "Identify defaults, fallbacks, and dead fields",
      "priority": "P2",
      "objective": "Which calculated fields are ignored, and which outputs rely on static defaults rather than learned values?",
      "risk": "Dead or default-driven logic may contradict architectural claims.",
      "scope": {
        "files": ["src/engine/*.py", "scripts/*.py", "src/app/server.py", "src/app/static/index.html"],
        "tables_or_sheets": ["NOT_APPLICABLE"],
        "fields": ["all constants, defaults, calculated fields, response fields"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["LIN-001"],
      "procedure": [
        "Trace assignments to their consumers and identify never-read fields.",
        "Catalog numeric and categorical defaults with activation conditions.",
        "Compare defaults with documentation and learned parameter ranges."
      ],
      "suggested_commands": ["Use static reference searches and controlled calls that activate each fallback."],
      "assertions": ["Every active default is documented and visible when used.", "Fields claimed as model inputs are actually consumed."],
      "reconciliation": {
        "source_measure": "declared/calculated fields and defaults",
        "target_measure": "consumer references and runtime activation",
        "grain": "field/default",
        "tolerance": "exact reference accounting"
      },
      "evidence_required": ["Dead-field list", "default catalog", "activation samples", "file:line citations"],
      "completion_criteria": ["Every calculated field and default has a usage verdict."],
      "possible_issue_fingerprints": ["lineage:dead-field:<field>", "default:undocumented:<name>", "default:claimed-learned:<name>"],
      "estimated_effort": "medium"
    },
    {
      "id": "LEAK-001",
      "domain": "M. Split integrity and leakage",
      "title": "Reconstruct exact training, calibration, holdout, and test membership",
      "priority": "P0",
      "objective": "Which row keys enter each fit, calibration, evaluation, and competition-test operation?",
      "risk": "Ambiguous membership makes leakage impossible to exclude.",
      "scope": {
        "files": ["scripts/train_models.py", "scripts/evaluate_models.py", "src/engine/structural.py", "src/engine/residual.py", "lake/curated/weekly_market_panel.parquet"],
        "tables_or_sheets": ["weekly_market_panel"],
        "fields": ["week_start", "market", "dataset_split", "is_complete_week", "is_complete_guest_inputs"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["TEMP-003", "KEY-004"],
      "procedure": [
        "Materialize row-key sets in the temporary audit directory for each model operation.",
        "Compare intersections and omissions.",
        "Verify membership is reproducible from code and artifact metadata."
      ],
      "suggested_commands": ["Execute filter expressions read-only and hash sorted row-key lists."],
      "assertions": ["Each evaluation row is excluded from all relevant fitting operations.", "Membership sets are finite and reproducible."],
      "reconciliation": {
        "source_measure": "panel row keys",
        "target_measure": "partitioned role sets",
        "grain": "week_start/market/dataset_split",
        "tolerance": "exact partition under each operation"
      },
      "evidence_required": ["Role counts", "set hashes", "overlap and omission lists"],
      "completion_criteria": ["Every model operation has an explicit row-key population."],
      "possible_issue_fingerprints": ["leakage:population-overlap:<roles>:<key>", "split:unassigned-row:<key>", "split:nonreproducible-membership"],
      "estimated_effort": "medium"
    },
    {
      "id": "LEAK-002",
      "domain": "M. Split integrity and leakage",
      "title": "Audit target-bearing and realized planning inputs",
      "priority": "P0",
      "objective": "Would every planning feature and prior have been known on the planner's decision date?",
      "risk": "Realized PAX, load factor, P2P, arrivals, or guests in planning inputs invalidates the planning claim.",
      "scope": {
        "files": ["src/engine/*.py", "scripts/train_models.py", "scripts/evaluate_models.py", "src/app/server.py"],
        "tables_or_sheets": ["model and simulator inputs"],
        "fields": ["seats", "pax", "load_factor", "p2p", "p2p_share", "new_arrivals", "guests", "priors"],
        "date_or_population": "planning-mode evaluation and live scenarios"
      },
      "prerequisites": ["LEAK-001", "LIN-002"],
      "procedure": [
        "Classify each input as scheduled, known-calendar, historical prior, realized, target-derived, or planner override.",
        "Trace values used for every planning-mode prediction.",
        "Compare with realized-chain diagnostic inputs and labels."
      ],
      "suggested_commands": ["Instrument or reproduce a fixed evaluation row and list all accessed values."],
      "assertions": ["Planning predictions use scheduled seats and training-only priors, not holdout realized chain values.", "Diagnostic modes remain separately labeled."],
      "reconciliation": {
        "source_measure": "actual runtime input values",
        "target_measure": "decision-time allowed input set",
        "grain": "prediction/input",
        "tolerance": "0 prohibited inputs"
      },
      "evidence_required": ["Input classification matrix", "runtime trace", "violating rows and fields"],
      "completion_criteria": ["Every planning input has a decision-time availability verdict."],
      "possible_issue_fingerprints": ["leakage:realized-planning-input:<field>", "leakage:target-derived-prior:<field>", "mode:planning-realized-conflated"],
      "estimated_effort": "large"
    },
    {
      "id": "LEAK-003",
      "domain": "M. Split integrity and leakage",
      "title": "Audit preprocessing, tuning, and model-selection leakage",
      "priority": "P0",
      "objective": "Do scaling, imputation, feature selection, top-N markets, hyperparameters, or model choice use holdout/test information?",
      "risk": "Indirect leakage inflates reported performance.",
      "scope": {
        "files": ["src/engine/*.py", "scripts/*.py", "lake/curated/*.json"],
        "tables_or_sheets": ["model inputs and evaluation outputs"],
        "fields": ["all fitted transforms, market lists, parameters, model choices"],
        "date_or_population": "ALL fitting and evaluation windows"
      },
      "prerequisites": ["LEAK-001", "LIN-002", "CAT-003"],
      "procedure": [
        "Locate every data-dependent selection or fitted statistic.",
        "Identify its fit population and whether evaluation results influenced its choice.",
        "Check top-15 ranking and archetype selection against training-only data."
      ],
      "suggested_commands": ["rg -n 'fit|select|top|sort_values|GridSearch|cross_val|best|mean|median|std|quantile' engine scripts"],
      "assertions": ["All data-dependent choices use training-only evidence or are explicitly prespecified.", "Temporal data are not tuned with random cross-validation."],
      "reconciliation": {
        "source_measure": "allowed training rows",
        "target_measure": "rows used by each fitted choice",
        "grain": "operation/row key",
        "tolerance": "0 prohibited rows"
      },
      "evidence_required": ["Fitted-operation inventory", "fit populations", "code citations", "selection history if available"],
      "completion_criteria": ["Every learned preprocessing or selection step has a leakage verdict."],
      "possible_issue_fingerprints": ["leakage:global-preprocessing:<operation>", "leakage:test-guided-selection:<choice>", "leakage:random-cv-temporal"],
      "estimated_effort": "large"
    },
    {
      "id": "LEAK-004",
      "domain": "M. Split integrity and leakage",
      "title": "Test conformal calibration and evaluation separation",
      "priority": "P0",
      "objective": "Were uncertainty margins fitted and assessed on temporally distinct observations?",
      "risk": "Using the same residuals for calibration and coverage makes coverage claims circular.",
      "scope": {
        "files": ["scripts/train_models.py", "scripts/evaluate_models.py", "src/engine/uncertainty.py", "lake/curated/conformal_calibrator.json"],
        "tables_or_sheets": ["calibration and holdout populations"],
        "fields": ["nonconformity scores", "market margins", "_target_alpha", "_demonstrated_holdout_coverage"],
        "date_or_population": "ALL calibration and coverage rows"
      },
      "prerequisites": ["LEAK-001", "UNC-001"],
      "procedure": [
        "Reconstruct row keys used to estimate each conformal margin.",
        "Reconstruct row keys used to report demonstrated coverage.",
        "Compute their intersection and verify evaluation code does not overwrite calibration evidence with holdout-derived values."
      ],
      "suggested_commands": ["Trace conformal JSON writes and compare row-key hashes for calibration and coverage."],
      "assertions": ["Calibration and evaluation sets are disjoint or use a valid cross-conformal design.", "Coverage metadata provenance is explicit."],
      "reconciliation": {
        "source_measure": "calibration row keys",
        "target_measure": "coverage-evaluation row keys",
        "grain": "week_start/market",
        "tolerance": "0 overlap unless every row belongs to a documented cross-conformal fold"
      },
      "evidence_required": ["Row-key sets and hashes", "intersection", "write-path citations", "recomputed coverage"],
      "completion_criteria": ["Calibration/evaluation separation is proven or contradicted."],
      "possible_issue_fingerprints": ["uncertainty:calibration-evaluation-overlap", "uncertainty:holdout-writes-calibrator", "uncertainty:coverage-circular"],
      "estimated_effort": "large"
    },
    {
      "id": "MET-001",
      "domain": "N. Target and metric validity",
      "title": "Establish the exact prediction target and units",
      "priority": "P0",
      "objective": "Does Guests represent daily stock, guest-days, persons, room nights, or another quantity at each layer?",
      "risk": "A unit or target mismatch makes model outputs unusable for hotel planning.",
      "scope": {
        "files": ["Data_Dictionary.pdf", "README.md", "docs/*.md", "src/engine/*.py", "src/app/static/index.html"],
        "tables_or_sheets": ["raw guest files", "weekly_market_panel"],
        "fields": ["Guests", "guests", "new_arrivals", "same_day_guests", "baseline_los", "sim_guests"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["RAW-003", "LIN-001", "NUM-003"],
      "procedure": [
        "Collect every target definition and unit label.",
        "Trace daily-to-weekly aggregation and LOS multiplication.",
        "Identify semantic changes or unsupported conversions."
      ],
      "suggested_commands": ["rg -n 'guest-days|guest nights|Guests|New Arrivals|LOS|length of stay' README.md docs engine app"],
      "assertions": ["The target has one explicit unit at every stage.", "Guest stock is not mislabeled as unique arrivals or room nights."],
      "reconciliation": {
        "source_measure": "raw target definition and daily values",
        "target_measure": "weekly/model/UI target",
        "grain": "field/stage",
        "tolerance": "exact unit and aggregation lineage"
      },
      "evidence_required": ["Definition citations", "unit lineage", "worked weekly example", "contradictory labels"],
      "completion_criteria": ["Every target-bearing surface has a supported semantic definition."],
      "possible_issue_fingerprints": ["target:unit-mismatch:<stage>", "target:stock-flow-confusion", "target:guest-days-room-nights-confusion"],
      "estimated_effort": "medium"
    },
    {
      "id": "MET-002",
      "domain": "N. Target and metric validity",
      "title": "Independently reproduce WMAPE, bias, MAE, and RMSE",
      "priority": "P0",
      "objective": "Do metric formulas, sign conventions, denominators, units, and population filters match reported results?",
      "risk": "Incorrect metrics invalidate headline accuracy claims.",
      "scope": {
        "files": ["scripts/evaluate_models.py", "lake/curated/evaluation_results.json"],
        "tables_or_sheets": ["evaluation observations"],
        "fields": ["actual", "prediction", "wmape", "bias", "mae", "rmse"],
        "date_or_population": "Every reported diagnostic, benchmark, market, and season population"
      },
      "prerequisites": ["LEAK-001", "MET-001"],
      "procedure": [
        "Retain observation-level actuals and predictions without modifying artifacts.",
        "Apply independently written formulas.",
        "Test zero-target, low-volume, negative-prediction, and empty-population behavior."
      ],
      "suggested_commands": ["Compute sum(abs(pred-actual))/sum(abs(actual)), signed sum(pred-actual)/sum(actual), MAE, and RMSE independently."],
      "assertions": ["Metric formulas and bias direction are documented and reproduced.", "Zero denominators do not become misleading perfect scores."],
      "reconciliation": {
        "source_measure": "observation-level actuals and predictions",
        "target_measure": "saved metrics",
        "grain": "population/metric",
        "tolerance": "absolute error <=5e-13 before rounding"
      },
      "evidence_required": ["Formula definitions", "observation counts", "metric diffs", "edge-case results"],
      "completion_criteria": ["Every reported metric is reproduced or contradicted."],
      "possible_issue_fingerprints": ["metric:wmape-formula", "metric:bias-sign", "metric:zero-denominator", "metric:population-filter:<name>"],
      "estimated_effort": "large"
    },
    {
      "id": "MET-003",
      "domain": "N. Target and metric validity",
      "title": "Evaluate complete-case and segment weighting effects",
      "priority": "P1",
      "objective": "How do exclusions and weighting affect domestic, international, market, season, volume-tier, archetype, and cold-start performance?",
      "risk": "Complete-case filtering or high-volume markets can make aggregate performance unrepresentative.",
      "scope": {
        "files": ["scripts/evaluate_models.py", "lake/curated/weekly_market_panel.parquet", "lake/curated/evaluation_results.json"],
        "tables_or_sheets": ["evaluation populations"],
        "fields": ["is_complete_week", "is_complete_guest_inputs", "market", "season", "archetype", "guests", "predictions"],
        "date_or_population": "holdout"
      },
      "prerequisites": ["MET-002", "MISS-003"],
      "procedure": [
        "Compare included and excluded observations by target volume, market, and missingness.",
        "Compute micro and macro metrics across required segments.",
        "Quantify domestic contribution to combined results."
      ],
      "suggested_commands": ["Produce inclusion propensity and segment metric tables from retained evaluation rows."],
      "assertions": ["Selection effects are visible.", "International planning performance is reported separately from domestic demand."],
      "reconciliation": {
        "source_measure": "all eligible chronological holdout rows",
        "target_measure": "reported complete-case population",
        "grain": "row and segment",
        "tolerance": "exact inclusion accounting"
      },
      "evidence_required": ["Included/excluded counts and volumes", "segment metrics", "domestic weighting contribution"],
      "completion_criteria": ["Every excluded row and major segment has a performance or availability explanation."],
      "possible_issue_fingerprints": ["metric:complete-case-selection:<segment>", "metric:domestic-masking", "metric:segment-omitted:<segment>"],
      "estimated_effort": "large"
    },
    {
      "id": "MET-004",
      "domain": "N. Target and metric validity",
      "title": "Validate baseline comparability and information parity",
      "priority": "P1",
      "objective": "Do baseline, calendar, structural, and hybrid models receive comparable information and evaluation rows?",
      "risk": "An unfair benchmark can overstate model improvement.",
      "scope": {
        "files": ["scripts/evaluate_models.py", "src/engine/residual.py", "lake/curated/evaluation_results.json"],
        "tables_or_sheets": ["benchmark populations"],
        "fields": ["baseline features", "calendar features", "structural inputs", "hybrid inputs", "predictions"],
        "date_or_population": "holdout"
      },
      "prerequisites": ["LEAK-002", "LEAK-003", "MET-002"],
      "procedure": [
        "List inputs, fit windows, target transformations, and populations for each benchmark.",
        "Confirm predictions align to identical row keys.",
        "Recompute relative improvements and uncertainty around differences."
      ],
      "suggested_commands": ["Compare row-key hashes and feature-availability matrices across benchmark models."],
      "assertions": ["Benchmark comparisons use identical targets and rows.", "Any information advantage is disclosed."],
      "reconciliation": {
        "source_measure": "benchmark row keys and target values",
        "target_measure": "model-specific evaluation rows",
        "grain": "model/row key",
        "tolerance": "exact row and target parity"
      },
      "evidence_required": ["Information-parity matrix", "row-key comparison", "metric deltas", "paired-error distribution"],
      "completion_criteria": ["Every benchmark difference is attributable to model behavior or explicitly disclosed information differences."],
      "possible_issue_fingerprints": ["benchmark:population-mismatch:<models>", "benchmark:information-advantage:<model>", "benchmark:target-mismatch:<model>"],
      "estimated_effort": "medium"
    },
    {
      "id": "STAT-001",
      "domain": "O. Statistical and model-input data quality",
      "title": "Measure temporal, market-mix, and volume distribution shift",
      "priority": "P1",
      "objective": "How do feature, target, market share, and volume distributions change across training, holdout, and competition test?",
      "risk": "Performance may not generalize under structural drift.",
      "scope": {
        "files": ["lake/curated/weekly_market_panel.parquet"],
        "tables_or_sheets": ["weekly_market_panel"],
        "fields": ["all model inputs", "guests", "market", "season", "archetype"],
        "date_or_population": "train versus holdout versus competition test"
      },
      "prerequisites": ["LEAK-001", "MISS-003"],
      "procedure": [
        "Compare quantiles, categorical shares, missingness, and target distributions.",
        "Calculate transparent drift measures and retain per-segment results.",
        "Identify structural breaks and new/disappearing markets."
      ],
      "suggested_commands": ["Compute PSI, standardized mean differences, KS statistics, and categorical share deltas as descriptive diagnostics."],
      "assertions": ["Material drift is reported by field and segment.", "Drift statistics are not treated as causal proof."],
      "reconciliation": {
        "source_measure": "training distributions",
        "target_measure": "later-split distributions",
        "grain": "field/segment",
        "tolerance": "Report distributions; materiality threshold requires owner confirmation"
      },
      "evidence_required": ["Distribution tables", "drift measures", "time plots or numeric break summaries"],
      "completion_criteria": ["Every model input and target has a split-drift result."],
      "possible_issue_fingerprints": ["drift:feature:<field>:<split>", "drift:market-mix:<split>", "drift:target:<segment>"],
      "estimated_effort": "large"
    },
    {
      "id": "STAT-002",
      "domain": "O. Statistical and model-input data quality",
      "title": "Assess sparse cells, unstable ratios, and multicollinearity",
      "priority": "P1",
      "objective": "Which market-season parameters or residual features are weakly supported or unstable?",
      "risk": "Sparse or collinear inputs can produce brittle estimates and false precision.",
      "scope": {
        "files": ["lake/curated/weekly_market_panel.parquet", "lake/curated/structural_calibration.json", "src/engine/residual.py"],
        "tables_or_sheets": ["weekly_market_panel"],
        "fields": ["market", "season", "historical_weeks", "seats", "pax", "p2p", "new_arrivals", "guests", "all residual features"],
        "date_or_population": "training"
      },
      "prerequisites": ["BRG-002", "LIN-002"],
      "procedure": [
        "Count observations and nonzero denominators per market-season cell.",
        "Bootstrap ratios and parameters by time block.",
        "Measure correlations, condition numbers, and feature variance."
      ],
      "suggested_commands": ["Use training-only block resampling in a temporary process."],
      "assertions": ["Sparse or unstable parameters are identifiable from retained evidence.", "Reported precision reflects effective sample size."],
      "reconciliation": {
        "source_measure": "training market-week observations",
        "target_measure": "parameter estimates and model features",
        "grain": "market/season/parameter",
        "tolerance": "Report distributions; stability threshold requires owner confirmation"
      },
      "evidence_required": ["Cell counts", "bootstrap intervals", "correlation and condition diagnostics", "zero-variance fields"],
      "completion_criteria": ["Every calibrated cell and feature has a support/stability result."],
      "possible_issue_fingerprints": ["statistics:sparse-cell:<market>:<season>", "statistics:unstable-ratio:<parameter>", "statistics:multicollinearity:<features>"],
      "estimated_effort": "large"
    },
    {
      "id": "STAT-003",
      "domain": "O. Statistical and model-input data quality",
      "title": "Profile residuals and sensitivity to analytical choices",
      "priority": "P1",
      "objective": "Do errors show temporal, market, seasonal, or volume structure, and are results robust to cutoffs, grain, and outlier policies?",
      "risk": "Structured residuals and fragile choices undermine model and uncertainty assumptions.",
      "scope": {
        "files": ["scripts/evaluate_models.py", "src/engine/residual.py", "lake/curated/weekly_market_panel.parquet"],
        "tables_or_sheets": ["evaluation observations"],
        "fields": ["residual", "market", "season", "week_start", "volume", "archetype"],
        "date_or_population": "training and holdout"
      },
      "prerequisites": ["MET-002", "STAT-001", "STAT-002"],
      "procedure": [
        "Compute residual distributions, autocorrelation, bias, and variance by required segments.",
        "Repeat evaluation across a finite prespecified set of cutoff, outlier, market-list, and aggregation alternatives.",
        "Include structural-only and residual-layer ablations."
      ],
      "suggested_commands": ["Use temporary outputs only; do not overwrite saved models or metrics."],
      "assertions": ["Residual dependence and heteroskedasticity are quantified.", "Central claims are not based on one favorable analytical choice."],
      "reconciliation": {
        "source_measure": "reference evaluation metrics",
        "target_measure": "sensitivity and ablation metrics",
        "grain": "configuration/segment/metric",
        "tolerance": "Report full result range; materiality requires owner confirmation"
      },
      "evidence_required": ["Residual diagnostics", "configuration table", "ablation and sensitivity results"],
      "completion_criteria": ["All prespecified alternatives run or have a documented execution blocker."],
      "possible_issue_fingerprints": ["residual:autocorrelation:<segment>", "residual:segment-bias:<segment>", "model:choice-sensitive:<choice>"],
      "estimated_effort": "large"
    },
    {
      "id": "UNC-001",
      "domain": "P. Uncertainty and simulation inputs",
      "title": "Trace uncertainty calibration populations and quantities",
      "priority": "P0",
      "objective": "What observations fit uncertainty margins, and do intervals represent levels, incremental effects, parameters, or mixtures?",
      "risk": "An interval calibrated for one quantity cannot support a different claim.",
      "scope": {
        "files": ["scripts/train_models.py", "scripts/evaluate_models.py", "src/engine/uncertainty.py", "lake/curated/conformal_calibrator.json"],
        "tables_or_sheets": ["calibration observations"],
        "fields": ["market margins", "_target_alpha", "p10", "p50", "p90", "delta_p10", "delta_p50", "delta_p90"],
        "date_or_population": "ALL uncertainty fitting and evaluation rows"
      },
      "prerequisites": ["LEAK-001", "MET-001"],
      "procedure": [
        "Trace score definitions, denominators, quantiles, and fitting rows.",
        "Map each returned interval field to the quantity actually calibrated.",
        "Identify any reuse of level margins for incremental-effect claims."
      ],
      "suggested_commands": ["Inspect all conformal score calculations and JSON writes; recompute scores independently."],
      "assertions": ["Each interval has a precise estimand and calibration provenance.", "Level and delta uncertainty are not conflated."],
      "reconciliation": {
        "source_measure": "calibration scores and target alpha",
        "target_measure": "saved margins and runtime bounds",
        "grain": "market/interval type",
        "tolerance": "quantiles reproduced under the documented finite-sample rule"
      },
      "evidence_required": ["Score formulas", "row-key populations", "quantile reproduction", "estimand matrix"],
      "completion_criteria": ["Every interval field has an evidenced calibration meaning."],
      "possible_issue_fingerprints": ["uncertainty:estimand-mismatch:<field>", "uncertainty:delta-uses-level-margin", "uncertainty:quantile-rule-undocumented"],
      "estimated_effort": "large"
    },
    {
      "id": "UNC-002",
      "domain": "P. Uncertainty and simulation inputs",
      "title": "Measure empirical interval coverage and width by segment",
      "priority": "P0",
      "objective": "What coverage and width are demonstrated overall and by market, season, archetype, volume, and cold-start status?",
      "risk": "Overall 66.7% coverage may conceal severely undercovered segments and does not support an 80% label.",
      "scope": {
        "files": ["scripts/evaluate_models.py", "lake/curated/evaluation_results.json", "lake/curated/conformal_calibrator.json"],
        "tables_or_sheets": ["holdout observations"],
        "fields": ["actual", "lower", "upper", "coverage", "width", "market", "season", "archetype"],
        "date_or_population": "temporally separate holdout"
      },
      "prerequisites": ["UNC-001", "LEAK-004"],
      "procedure": [
        "Recompute inclusion indicators and absolute/relative interval widths.",
        "Report binomial uncertainty for coverage overall and by prespecified segment.",
        "Identify empty and low-sample segments."
      ],
      "suggested_commands": ["Compute exact counts and Wilson or exact binomial intervals without changing artifacts."],
      "assertions": ["Nominal coverage is distinguished from demonstrated coverage.", "Coverage is accompanied by width and sample size."],
      "reconciliation": {
        "source_measure": "holdout actuals and independently reconstructed bounds",
        "target_measure": "reported coverage",
        "grain": "segment",
        "tolerance": "exact inclusion counts; numeric rate follows count/sample size"
      },
      "evidence_required": ["Coverage counts", "width distributions", "confidence intervals", "undercovered segment list"],
      "completion_criteria": ["Overall and required-segment coverage and width are reported."],
      "possible_issue_fingerprints": ["uncertainty:nominal-mislabeled-demonstrated", "uncertainty:undercoverage:<segment>", "uncertainty:width-omitted:<segment>"],
      "estimated_effort": "large"
    },
    {
      "id": "UNC-003",
      "domain": "P. Uncertainty and simulation inputs",
      "title": "Validate bounded draws and dependence assumptions",
      "priority": "P1",
      "objective": "Do load factor, P2P share, multiplier, LOS, and residual draws obey bounds and realistic dependence?",
      "risk": "Independent or clipped draws can distort scenario risk and tail behavior.",
      "scope": {
        "files": ["src/engine/uncertainty.py", "src/engine/archetypes.py"],
        "tables_or_sheets": ["NOT_APPLICABLE"],
        "fields": ["load factor draws", "P2P draws", "multiplier shocks", "LOS shocks", "residual samples"],
        "date_or_population": "Representative supported and cold-start scenarios"
      },
      "prerequisites": ["UNC-001", "STAT-003"],
      "procedure": [
        "Generate deterministic draw samples for fixed scenarios.",
        "Test physical bounds, clipping mass, empirical correlations, and consistency with historical joint behavior.",
        "Compare assumed and observed marginal variability."
      ],
      "suggested_commands": ["Invoke run_monte_carlo with fixed seeds and inspect draw-generation components in a temporary harness."],
      "assertions": ["Bounded quantities remain within physical limits.", "Independence assumptions are documented and tested against history."],
      "reconciliation": {
        "source_measure": "historical joint distributions and configured priors",
        "target_measure": "simulation draw distributions",
        "grain": "market/season/parameter",
        "tolerance": "hard bounds exact; distribution differences reported for owner confirmation"
      },
      "evidence_required": ["Draw summaries", "bound violations", "clipping rates", "correlation comparisons"],
      "completion_criteria": ["Every stochastic input has a bound and dependence verdict."],
      "possible_issue_fingerprints": ["uncertainty:bound-violation:<parameter>", "uncertainty:clipping-mass:<parameter>", "uncertainty:unsupported-independence:<parameters>"],
      "estimated_effort": "medium"
    },
    {
      "id": "UNC-004",
      "domain": "P. Uncertainty and simulation inputs",
      "title": "Validate residual resampling and extreme-scenario behavior",
      "priority": "P1",
      "objective": "Does residual sampling preserve market and temporal structure, and do extreme or cold-start scenarios widen or warn appropriately?",
      "risk": "Residual reuse or fixed margins can understate uncertainty exactly where decisions are least supported.",
      "scope": {
        "files": ["src/engine/uncertainty.py", "src/engine/simulator.py", "lake/curated/residual_engine.pkl"],
        "tables_or_sheets": ["residual histories"],
        "fields": ["residual_history", "block_size", "conformal_margin", "is_cold_start", "interval width"],
        "date_or_population": "Supported, sparse, cold-start, closure, and extreme positive scenarios"
      },
      "prerequisites": ["UNC-002", "UNC-003"],
      "procedure": [
        "Trace residual ordering, market partitioning, and block-bootstrap implementation.",
        "Compare residual autocorrelation before and after resampling.",
        "Compare uncertainty widths and warnings across increasingly unsupported scenarios."
      ],
      "suggested_commands": ["Run deterministic scenario grids and calculate relative interval width."],
      "assertions": ["Residual samples preserve the claimed dependence structure.", "Unsupported or extreme scenarios are not more certain than well-supported baselines without evidence."],
      "reconciliation": {
        "source_measure": "historical residual dependence and support level",
        "target_measure": "resampled dependence and scenario interval width",
        "grain": "market/scenario",
        "tolerance": "Dependence and width distributions reported; business threshold requires owner confirmation"
      },
      "evidence_required": ["Residual-order evidence", "autocorrelation comparison", "scenario width table", "warning behavior"],
      "completion_criteria": ["Residual method and support-sensitive uncertainty are fully characterized."],
      "possible_issue_fingerprints": ["uncertainty:residual-order-lost", "uncertainty:cold-start-not-wider", "uncertainty:extreme-scenario-no-warning"],
      "estimated_effort": "large"
    },
    {
      "id": "SCEN-001",
      "domain": "Q. Scenario invariants and adversarial data cases",
      "title": "Test no-change and domestic-decoupling invariants",
      "priority": "P0",
      "objective": "Does a zero-lever scenario reproduce baseline exactly, and do international flight levers leave domestic demand unchanged?",
      "risk": "Failure means the simulator changes demand without a planning action or mixes incompatible domains.",
      "scope": {
        "files": ["src/engine/structural.py", "src/engine/simulator.py"],
        "tables_or_sheets": ["NOT_APPLICABLE"],
        "fields": ["all baseline, simulated, delta, and waterfall fields"],
        "date_or_population": "Every calibrated market-season plus DOMESTIC"
      },
      "prerequisites": ["REC-005"],
      "procedure": [
        "Run zero-lever scenarios across all supported combinations.",
        "Apply frequency, gauge, seats, load-factor, and P2P levers to DOMESTIC.",
        "Compare all output fields with baselines."
      ],
      "suggested_commands": ["Use direct engine calls with fixed seeds and no artifact writes."],
      "assertions": ["Zero levers produce zero structural and hybrid delta.", "International aviation levers produce zero domestic effect."],
      "reconciliation": {
        "source_measure": "baseline values",
        "target_measure": "zero-lever simulated values",
        "grain": "market/season/field",
        "tolerance": "absolute error <=1e-9"
      },
      "evidence_required": ["Scenario matrix", "maximum invariant error", "failing field samples"],
      "completion_criteria": ["Every supported market-season and domestic lever family is tested."],
      "possible_issue_fingerprints": ["scenario:no-change-drift:<market>:<season>", "scenario:domestic-flight-coupling:<lever>"],
      "estimated_effort": "medium"
    },
    {
      "id": "SCEN-002",
      "domain": "Q. Scenario invariants and adversarial data cases",
      "title": "Test monotonicity, route closure, and double-counting",
      "priority": "P0",
      "objective": "Do capacity changes have coherent direction without double-counting frequency, gauge, and direct seat changes?",
      "risk": "Nonsensical directional effects undermine planning use.",
      "scope": {
        "files": ["src/engine/structural.py", "src/engine/simulator.py"],
        "tables_or_sheets": ["NOT_APPLICABLE"],
        "fields": ["delta_frequency", "aircraft_gauge", "delta_seats_pct", "sim_seats", "sim_guests", "hybrid_delta"],
        "date_or_population": "Representative markets in every archetype"
      },
      "prerequisites": ["SCEN-001"],
      "procedure": [
        "Run ordered positive and negative lever grids.",
        "Run exact route closure and zero-seat cases.",
        "Compare combined frequency/gauge/seat effects to the documented formula and isolated effects."
      ],
      "suggested_commands": ["Invoke structural and hybrid simulation over a finite parameter grid."],
      "assertions": ["More nonnegative capacity cannot reduce structural demand absent an explicit opposing lever.", "Zero seats create zero aviation-chain demand.", "Seat changes are applied exactly once."],
      "reconciliation": {
        "source_measure": "documented seat and conversion equations",
        "target_measure": "scenario outputs",
        "grain": "scenario",
        "tolerance": "absolute error <=1e-9"
      },
      "evidence_required": ["Input/output grid", "formula reproduction", "monotonicity and closure failures"],
      "completion_criteria": ["Every archetype passes or has enumerated counterexamples."],
      "possible_issue_fingerprints": ["scenario:monotonicity:<market>:<lever>", "scenario:closure-positive-demand:<market>", "scenario:seat-double-count:<scenario>"],
      "estimated_effort": "medium"
    },
    {
      "id": "SCEN-003",
      "domain": "Q. Scenario invariants and adversarial data cases",
      "title": "Test physical bounds and waterfall identity",
      "priority": "P0",
      "objective": "Do all outputs remain physical and do waterfall components exactly reconcile to total lift?",
      "risk": "Invalid shares, negative demand, or unreconciled attribution misleads planners.",
      "scope": {
        "files": ["src/engine/structural.py", "src/engine/simulator.py", "src/app/server.py"],
        "tables_or_sheets": ["NOT_APPLICABLE"],
        "fields": ["load_factor", "p2p_share", "multiplier", "los", "all counts", "waterfall components", "total_lift"],
        "date_or_population": "Boundary and extreme finite input grid"
      },
      "prerequisites": ["SCEN-002"],
      "procedure": [
        "Exercise lower, upper, and beyond-boundary inputs for every lever.",
        "Test non-negativity and share bounds.",
        "Sum waterfall components and compare with structural total change."
      ],
      "suggested_commands": ["Use direct engine and API calls for a finite adversarial matrix."],
      "assertions": ["Shares remain in [0,1], counts remain nonnegative, and LOS respects documented bounds.", "Waterfall sum equals delta_guests."],
      "reconciliation": {
        "source_measure": "sum of five waterfall effects",
        "target_measure": "delta_guests",
        "grain": "scenario",
        "tolerance": "absolute error <=1e-8"
      },
      "evidence_required": ["Boundary matrix", "bound violations", "maximum waterfall residual"],
      "completion_criteria": ["All fields and every lever boundary are exercised."],
      "possible_issue_fingerprints": ["scenario:share-out-of-bounds:<field>", "scenario:negative-output:<field>", "scenario:waterfall-residual:<scenario>"],
      "estimated_effort": "medium"
    },
    {
      "id": "SCEN-004",
      "domain": "Q. Scenario invariants and adversarial data cases",
      "title": "Adversarially test API types, categories, and nonfinite inputs",
      "priority": "P1",
      "objective": "Does the API reject malformed, unknown, infinite, NaN, missing, and extreme inputs with safe, visible behavior?",
      "risk": "Weak validation can yield silent fallbacks, invalid JSON, or misleading scenarios.",
      "scope": {
        "files": ["src/app/server.py", "src/engine/structural.py", "src/engine/uncertainty.py"],
        "tables_or_sheets": ["GET /api/simulate"],
        "fields": ["market", "season", "delta_freq", "gauge", "delta_seats_pct", "delta_lf", "delta_p2p", "delta_mult_pct", "delta_los"],
        "date_or_population": "Finite adversarial request corpus"
      },
      "prerequisites": ["SCEN-003"],
      "procedure": [
        "Send missing, repeated, malformed, NaN, infinity, huge, negative, unknown-market, and invalid-season values.",
        "Record status, response schema, fallback visibility, and whether outputs serialize as valid JSON.",
        "Confirm no stack traces or local paths are exposed."
      ],
      "suggested_commands": ["Invoke DigitalTwinHandler with a local mock handler or localhost requests."],
      "assertions": ["Invalid values receive deterministic 4xx responses or explicitly documented bounded behavior.", "Unknown markets visibly report cold-start fallback."],
      "reconciliation": {
        "source_measure": "adversarial request cases",
        "target_measure": "expected validation outcomes",
        "grain": "request",
        "tolerance": "exact status and response contract"
      },
      "evidence_required": ["Request corpus", "status/response table", "unsafe outputs or disclosures"],
      "completion_criteria": ["Every parameter has type, boundary, null, and unknown-category tests."],
      "possible_issue_fingerprints": ["api:accepts-nonfinite:<field>", "api:unbounded:<field>", "api:silent-unknown-market:<value>", "api:error-disclosure"],
      "estimated_effort": "medium"
    },
    {
      "id": "REPRO-001",
      "domain": "R. Artifact, manifest, and reproducibility integrity",
      "title": "Validate manifest hashes, counts, and completeness",
      "priority": "P1",
      "objective": "Does manifest.json accurately identify all source and curated artifacts, hashes, sizes, checks, code revision, and configuration?",
      "risk": "An incomplete manifest cannot establish artifact provenance or staleness.",
      "scope": {
        "files": ["lake/manifest.json", "01a - DCT Dataset/*", "lake/curated/*", "lake/analytics.duckdb"],
        "tables_or_sheets": ["NOT_APPLICABLE"],
        "fields": ["sources", "curated_tables", "database", "checks", "format_version"],
        "date_or_population": "Current working tree"
      },
      "prerequisites": ["INV-002"],
      "procedure": [
        "Recompute source sizes and SHA-256 hashes.",
        "Recompute stated checks independently.",
        "Identify missing curated hashes, code revision, configuration, package versions, and generation timestamps."
      ],
      "suggested_commands": ["shasum -a 256 '01a - DCT Dataset'/* lake/curated/*; git rev-parse HEAD"],
      "assertions": ["Every recorded value matches current files.", "All inputs needed to identify a build are recorded or explicitly missing."],
      "reconciliation": {
        "source_measure": "current file metadata and independently recomputed checks",
        "target_measure": "manifest values",
        "grain": "manifest entry",
        "tolerance": "exact hashes, sizes, and integer counts; 1e-12 for floating checks"
      },
      "evidence_required": ["Hash comparison", "check diff", "missing provenance-field list"],
      "completion_criteria": ["Every manifest field is verified and omissions are enumerated."],
      "possible_issue_fingerprints": ["manifest:hash-mismatch:<path>", "manifest:missing-artifact:<path>", "manifest:missing-code-revision", "manifest:stale-check:<name>"],
      "estimated_effort": "medium"
    },
    {
      "id": "REPRO-002",
      "domain": "R. Artifact, manifest, and reproducibility integrity",
      "title": "Perform isolated clean rebuild comparison",
      "priority": "P0",
      "objective": "Can committed artifacts be reproduced from source data and code without relying on existing lake state?",
      "risk": "Non-reproducible artifacts make all saved evidence suspect.",
      "scope": {
        "files": ["Makefile", "requirements.txt", "scripts/build_lake.py", "scripts/build_panels.py", "scripts/train_models.py", "scripts/evaluate_models.py", "lake/**/*"],
        "tables_or_sheets": ["ALL generated objects"],
        "fields": ["ALL"],
        "date_or_population": "Complete build"
      },
      "prerequisites": ["REPRO-001", "REC-006"],
      "procedure": [
        "Copy only declared source inputs and code into a dedicated temporary audit directory.",
        "Run the documented build sequence with fixed environment and seeds.",
        "Compare schemas, sorted content hashes, metrics, and model predictions to repository artifacts."
      ],
      "suggested_commands": ["Run documented Makefile or Python commands only inside the temporary copy; never overwrite repository artifacts."],
      "assertions": ["A clean build completes from declared inputs.", "Any byte or semantic differences are quantified and attributable."],
      "reconciliation": {
        "source_measure": "repository artifacts",
        "target_measure": "isolated rebuild artifacts",
        "grain": "artifact/schema/row/metric/scenario",
        "tolerance": "exact semantic content; byte identity where deterministic serialization is claimed"
      },
      "evidence_required": ["Environment lock", "commands", "logs", "artifact hashes", "semantic diff"],
      "completion_criteria": ["All declared artifacts are compared or a precise blocker is recorded."],
      "possible_issue_fingerprints": ["rebuild:failure:<stage>", "rebuild:semantic-drift:<artifact>", "rebuild:undeclared-input:<path>"],
      "estimated_effort": "large"
    },
    {
      "id": "REPRO-003",
      "domain": "R. Artifact, manifest, and reproducibility integrity",
      "title": "Test deterministic seeds and execution-order independence",
      "priority": "P1",
      "objective": "Do repeated builds and scenarios remain stable across process starts and valid command orders?",
      "risk": "Hidden randomness or mutable state can change recommendations.",
      "scope": {
        "files": ["src/engine/uncertainty.py", "src/engine/simulator.py", "src/engine/residual.py", "scripts/*.py"],
        "tables_or_sheets": ["NOT_APPLICABLE"],
        "fields": ["random seeds", "model parameters", "scenario outputs", "artifact hashes"],
        "date_or_population": "Repeated finite runs"
      },
      "prerequisites": ["REPRO-002"],
      "procedure": [
        "Repeat identical scenarios in fresh processes.",
        "Repeat isolated builds and compare semantic outputs.",
        "Run independent valid stages in different orders to detect hidden state or cache dependence."
      ],
      "suggested_commands": ["Use fresh local processes with controlled PYTHONHASHSEED and captured environment."],
      "assertions": ["Identical inputs and seeds produce identical results.", "Execution order does not alter outputs."],
      "reconciliation": {
        "source_measure": "first-run semantic outputs",
        "target_measure": "repeat and reordered-run outputs",
        "grain": "artifact or scenario field",
        "tolerance": "exact for JSON and scenario values; byte identity only where claimed"
      },
      "evidence_required": ["Run commands", "seeds", "process environments", "hash and field diffs"],
      "completion_criteria": ["At least three fresh-process repetitions and two valid orderings are compared."],
      "possible_issue_fingerprints": ["repro:nondeterministic:<artifact>", "repro:process-dependent:<scenario>", "repro:execution-order-dependent:<stage>"],
      "estimated_effort": "large"
    },
    {
      "id": "REPRO-004",
      "domain": "R. Artifact, manifest, and reproducibility integrity",
      "title": "Audit hidden local state and artifact compatibility",
      "priority": "P1",
      "objective": "Do builds or runtime depend on caches, current directory, modified artifacts, local paths, or undeclared package versions?",
      "risk": "A prototype may work only in the author's current checkout.",
      "scope": {
        "files": ["**/*.py", "requirements.txt", ".gitignore", "__pycache__/**/*", ".pytest_cache/**/*", "tmp/**/*", "lake/**/*"],
        "tables_or_sheets": ["NOT_APPLICABLE"],
        "fields": ["paths", "environment variables", "imports", "versions", "cache keys"],
        "date_or_population": "Current and isolated environments"
      },
      "prerequisites": ["INV-001", "REPRO-002"],
      "procedure": [
        "Search for absolute paths, implicit current-directory access, cache reads, and undeclared environment variables.",
        "Start from a different working directory in the isolated copy.",
        "Test missing, stale, and schema-incompatible artifacts for actionable errors."
      ],
      "suggested_commands": ["rg -n '/Users/|cwd|__pycache__|\\.cache|tmp|environ|getenv|Path\\(' . -g '*.py'"],
      "assertions": ["Runtime depends only on declared inputs and resolved repository paths.", "Incompatible artifacts fail safely rather than producing outputs."],
      "reconciliation": {
        "source_measure": "declared dependencies",
        "target_measure": "observed runtime file and environment accesses",
        "grain": "dependency",
        "tolerance": "0 undeclared material dependencies"
      },
      "evidence_required": ["Dependency-access inventory", "alternate-CWD result", "failure-mode samples", "working-tree state"],
      "completion_criteria": ["All material local-state dependencies and compatibility checks are characterized."],
      "possible_issue_fingerprints": ["repro:absolute-path:<file>", "repro:cache-dependent:<path>", "artifact:incompatible-loads-silently:<artifact>"],
      "estimated_effort": "medium"
    },
    {
      "id": "CONS-001",
      "domain": "S. Cross-surface consistency",
      "title": "Compare headline metrics and uncertainty claims",
      "priority": "P0",
      "objective": "Do README, documentation, JSON, reports, figures, API, and UI show identical metrics, populations, and coverage meanings?",
      "risk": "Conflicting headline numbers create immediate credibility failure.",
      "scope": {
        "files": ["README.md", "docs/*.md", "lake/curated/evaluation_results.json", "lake/curated/conformal_calibrator.json", "src/app/**/*", "output/**/*", "scripts/build_*report.py", "scripts/generate_scenario_charts.py"],
        "tables_or_sheets": ["evaluation results"],
        "fields": ["WMAPE", "bias", "MAE", "RMSE", "coverage", "P10", "P90"],
        "date_or_population": "ALL published claims"
      },
      "prerequisites": ["REC-006", "UNC-002"],
      "procedure": [
        "Extract every numeric metric and nearby population/mode label.",
        "Normalize display precision and compare underlying values.",
        "Verify nominal 80% and demonstrated 66.7% are not conflated."
      ],
      "suggested_commands": ["rg -n '26\\.05|23\\.49|22\\.10|20\\.91|66\\.7|80\\.0|WMAPE|coverage|RMSE|bias' README.md docs app scripts"],
      "assertions": ["Identical claims use identical values and populations.", "Every metric identifies planning, realized-chain, domestic, combined, or benchmark mode."],
      "reconciliation": {
        "source_measure": "reproduced evaluation values",
        "target_measure": "published values",
        "grain": "surface/claim",
        "tolerance": "documented display rounding only"
      },
      "evidence_required": ["Claim matrix", "file:line or report-page citations", "contradictions"],
      "completion_criteria": ["Every headline metric and uncertainty statement has a consistency verdict."],
      "possible_issue_fingerprints": ["claim:metric-conflict:<metric>:<surface>", "claim:coverage-mislabeled:<surface>", "claim:mode-omitted:<surface>"],
      "estimated_effort": "medium"
    },
    {
      "id": "CONS-002",
      "domain": "S. Cross-surface consistency",
      "title": "Compare windows, row counts, and market counts",
      "priority": "P1",
      "objective": "Are date ranges, week counts, observation counts, row counts, and market counts consistent across artifacts and documents?",
      "risk": "Conflicting populations indicate stale or mixed-generation evidence.",
      "scope": {
        "files": ["lake/manifest.json", "lake/curated/evaluation_results.json", "README.md", "docs/*.md", "src/app/**/*", "output/**/*"],
        "tables_or_sheets": ["ALL"],
        "fields": ["date ranges", "104/30 weeks", "1724/501 observations", "1768/510 observations", "row counts", "market counts"],
        "date_or_population": "ALL claims"
      },
      "prerequisites": ["INV-002", "REC-006"],
      "procedure": [
        "Extract all count and window claims with context.",
        "Recompute authoritative values from current artifacts.",
        "Separate total theoretical populations from complete-input populations."
      ],
      "suggested_commands": ["rg -n '[0-9,]+ rows|weeks|market-weeks|markets|202[2-6]' README.md docs app scripts"],
      "assertions": ["Each count states its filter and population.", "Current artifacts and published claims agree or are explicitly versioned."],
      "reconciliation": {
        "source_measure": "recomputed counts and ranges",
        "target_measure": "published claims",
        "grain": "claim/surface",
        "tolerance": "exact"
      },
      "evidence_required": ["Count/window matrix", "queries", "citations", "stale-claim list"],
      "completion_criteria": ["Every population claim is matched to a reproducible query."],
      "possible_issue_fingerprints": ["claim:count-conflict:<measure>", "claim:window-conflict:<population>", "claim:filter-undisclosed:<count>"],
      "estimated_effort": "medium"
    },
    {
      "id": "CONS-003",
      "domain": "S. Cross-surface consistency",
      "title": "Compare conversion-chain definitions and feature labels",
      "priority": "P0",
      "objective": "Do code, docs, API, UI, and reports describe origin, nationality, passengers, P2P, arrivals, multiplier, LOS, and guests consistently?",
      "risk": "Semantically inconsistent labels can cause planners to interpret estimates as observed causal quantities.",
      "scope": {
        "files": ["README.md", "docs/*.md", "src/engine/*.py", "src/app/**/*", "output/**/*"],
        "tables_or_sheets": ["NOT_APPLICABLE"],
        "fields": ["all conversion-chain fields and labels"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["BRG-001", "MET-001", "LIN-001"],
      "procedure": [
        "Extract definitions and equations from each surface.",
        "Compare them with implemented formulas and raw data semantics.",
        "Classify each statement as reproduced, inspected, claimed, or missing/contradicted."
      ],
      "suggested_commands": ["rg -n 'origin|nationality|seats|passengers|P2P|arrivals|multiplier|LOS|guest' README.md docs engine app"],
      "assertions": ["Departure country and nationality remain distinct.", "Effective multiplier is not decomposed into separately observed components.", "Target units remain consistent."],
      "reconciliation": {
        "source_measure": "implemented definitions",
        "target_measure": "surface definitions",
        "grain": "term/surface",
        "tolerance": "semantic equivalence required"
      },
      "evidence_required": ["Term-definition matrix", "equations", "file:line and report-page citations"],
      "completion_criteria": ["Every critical term has a cross-surface consistency verdict."],
      "possible_issue_fingerprints": ["claim:origin-nationality-equivalence:<surface>", "claim:multiplier-overdecomposed:<surface>", "claim:target-label-conflict:<surface>"],
      "estimated_effort": "large"
    },
    {
      "id": "CONS-004",
      "domain": "S. Cross-surface consistency",
      "title": "Compare defaults, domestic scope, and planning-mode labels",
      "priority": "P1",
      "objective": "Are simulator defaults, supported markets, domestic behavior, cold-start behavior, and planning-versus-realized modes consistent everywhere?",
      "risk": "A correct engine can still mislead if the interface or guide describes different behavior.",
      "scope": {
        "files": ["scripts/run_scenario.py", "src/engine/*.py", "src/app/server.py", "src/app/static/index.html", "README.md", "docs/*.md"],
        "tables_or_sheets": ["GET /api/simulate"],
        "fields": ["default market", "season", "gauge", "all lever defaults", "supported markets", "mode labels"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["BRG-003", "SCEN-001", "SCEN-004"],
      "procedure": [
        "Extract defaults and allowed values from CLI, API, UI, and guides.",
        "Run default requests and compare actual behavior.",
        "Check domestic and cold-start explanations and warnings."
      ],
      "suggested_commands": ["rg -n 'default|UNITED KINGDOM|Winter_Peak|250|DOMESTIC|cold.start|planning|realized' scripts engine app README.md docs"],
      "assertions": ["Defaults and units agree across surfaces.", "Domestic and cold-start behavior are visibly distinct.", "Planning and realized diagnostics are never presented interchangeably."],
      "reconciliation": {
        "source_measure": "runtime defaults and behavior",
        "target_measure": "documented and displayed defaults",
        "grain": "field/surface",
        "tolerance": "exact"
      },
      "evidence_required": ["Default matrix", "runtime samples", "label contradictions"],
      "completion_criteria": ["Every user-facing default and mode label has a consistency verdict."],
      "possible_issue_fingerprints": ["default:cross-surface-conflict:<field>", "scope:domestic-mislabeled:<surface>", "mode:planning-realized-label-conflict:<surface>"],
      "estimated_effort": "medium"
    },
    {
      "id": "TEST-001",
      "domain": "T. Tests and quality controls",
      "title": "Inventory what each existing test actually proves",
      "priority": "P2",
      "objective": "What assertion, fixture, population, and failure mode does every test cover?",
      "risk": "Test names and passing status can overstate actual validation.",
      "scope": {
        "files": ["tests/test_digital_twin.py"],
        "tables_or_sheets": ["NOT_APPLICABLE"],
        "fields": ["all test methods and assertions"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["INV-001"],
      "procedure": [
        "List each test, setup dependency, assertion, input, and covered contract.",
        "Identify whether it inspects committed artifacts or independently reconstructs expected behavior.",
        "Run tests read-only and retain output."
      ],
      "suggested_commands": [".venv/bin/python -m pytest -q tests/test_digital_twin.py"],
      "assertions": ["Every passing test is mapped only to the behavior it asserts.", "Artifact-dependent tests are not treated as independent source reconciliation."],
      "reconciliation": {
        "source_measure": "test methods",
        "target_measure": "test-coverage inventory records",
        "grain": "test",
        "tolerance": "100% coverage"
      },
      "evidence_required": ["Test inventory", "assertion citations", "test run output", "dependency classification"],
      "completion_criteria": ["Every test has a precise proof-scope statement."],
      "possible_issue_fingerprints": ["test:assertion-scope-overclaimed:<test>", "test:artifact-dependent:<test>", "test:nonrepresentative-fixture:<test>"],
      "estimated_effort": "medium"
    },
    {
      "id": "TEST-002",
      "domain": "T. Tests and quality controls",
      "title": "Detect tautological and missing critical tests",
      "priority": "P1",
      "objective": "Which tests duplicate implementation logic, and which critical contracts have no independent test?",
      "risk": "Tautological tests can pass while shared logic is wrong.",
      "scope": {
        "files": ["tests/test_digital_twin.py", "scripts/*.py", "src/engine/*.py", "src/app/server.py"],
        "tables_or_sheets": ["NOT_APPLICABLE"],
        "fields": ["data contracts", "leakage barriers", "conversion identities", "domestic separation", "cold start", "coverage", "metrics", "API", "rebuild"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["TEST-001", "LIN-001"],
      "procedure": [
        "Compare expected-value calculations in tests with production functions.",
        "Map required contracts to independent positive, negative, and adversarial tests.",
        "List uncovered or circularly tested behaviors."
      ],
      "suggested_commands": ["Cross-reference test assertions with production code and the required-domain checklist."],
      "assertions": ["Critical expected values are independently derived where feasible.", "Every central contract has at least one meaningful test or a documented gap."],
      "reconciliation": {
        "source_measure": "required critical contracts",
        "target_measure": "independent existing tests",
        "grain": "contract",
        "tolerance": "0 unreported gaps"
      },
      "evidence_required": ["Contract-to-test matrix", "tautology citations", "missing-test list"],
      "completion_criteria": ["All required contracts are mapped to adequate, inadequate, or absent tests."],
      "possible_issue_fingerprints": ["test:tautological:<test>", "test:missing-contract:<contract>", "test:no-negative-control:<contract>"],
      "estimated_effort": "medium"
    },
    {
      "id": "TEST-003",
      "domain": "T. Tests and quality controls",
      "title": "Verify an independent end-to-end test exists",
      "priority": "P1",
      "objective": "Does any test trace source evidence through panel, model, scenario, API, and UI without relying only on saved outputs?",
      "risk": "Layer-specific tests may miss integration defects.",
      "scope": {
        "files": ["tests/test_digital_twin.py", "01a - DCT Dataset/*", "lake/**/*", "src/engine/*.py", "src/app/**/*"],
        "tables_or_sheets": ["ALL"],
        "fields": ["representative end-to-end fields"],
        "date_or_population": "At least one international market-week and one adversarial case"
      },
      "prerequisites": ["TEST-001", "REC-007"],
      "procedure": [
        "Identify tests crossing all lifecycle stages.",
        "Check whether expected values originate from raw evidence rather than the same artifact under test.",
        "If absent, record the exact untested transitions without adding a test."
      ],
      "suggested_commands": ["Inspect fixtures and call graph; no repository edits."],
      "assertions": ["At least one independent vertical slice is tested or the absence is documented.", "Passing tests are not presented as statistical validation."],
      "reconciliation": {
        "source_measure": "required lifecycle transitions",
        "target_measure": "transitions covered by one independent test",
        "grain": "transition",
        "tolerance": "full coverage required for a claimed end-to-end test"
      },
      "evidence_required": ["Transition map", "fixture provenance", "assertion citations", "gap list"],
      "completion_criteria": ["End-to-end coverage is proven or explicitly classified missing."],
      "possible_issue_fingerprints": ["test:no-independent-e2e", "test:e2e-uses-same-artifact", "claim:tests-prove-statistical-validity"],
      "estimated_effort": "small"
    },
    {
      "id": "SEC-001",
      "domain": "U. Restricted-data and exposure review",
      "title": "Inventory committed and ignored restricted-data copies",
      "priority": "P0",
      "objective": "Are raw competition rows or duplicates committed, embedded in history, or copied into generated/static artifacts?",
      "risk": "Restricted-data exposure may violate competition rules.",
      "scope": {
        "files": [".gitignore", "git tracked files and history", "01a - DCT Dataset/*", "lake/**/*", "output/**/*", "tmp/**/*", "src/app/static/**/*"],
        "tables_or_sheets": ["ALL"],
        "fields": ["raw rows, extracts, hashes, filenames"],
        "date_or_population": "Current tree and reachable Git history"
      },
      "prerequisites": ["INV-001"],
      "procedure": [
        "Classify raw files and derived artifacts by restriction risk.",
        "Search tracked history and generated files for raw filenames, headers, and sampled exact rows.",
        "Identify duplication and ignore-rule gaps without rewriting history."
      ],
      "suggested_commands": ["git ls-files; git log --all --name-only; git grep; strings <binary> for targeted headers only"],
      "assertions": ["Every restricted source copy and extract is identified.", "Static or report artifacts do not reproduce restricted row-level data without authorization."],
      "reconciliation": {
        "source_measure": "restricted source files and sampled row fingerprints",
        "target_measure": "matches in committed/generated assets",
        "grain": "path/fingerprint",
        "tolerance": "0 unauthorized matches"
      },
      "evidence_required": ["Exposure inventory", "Git path/history citations", "matched fingerprints without publishing sensitive row content"],
      "completion_criteria": ["Current tree, history, static assets, reports, and caches are assessed."],
      "possible_issue_fingerprints": ["exposure:raw-committed:<path>", "exposure:raw-in-history:<path>", "exposure:row-in-generated:<path>"],
      "estimated_effort": "large"
    },
    {
      "id": "SEC-002",
      "domain": "U. Restricted-data and exposure review",
      "title": "Audit API and static web exposure",
      "priority": "P0",
      "objective": "Can API endpoints or static paths return raw rows, excessive detail, arbitrary local files, or exception traces?",
      "risk": "A local prototype may unintentionally expose restricted or sensitive data.",
      "scope": {
        "files": ["src/app/server.py", "src/app/static/**/*"],
        "tables_or_sheets": ["GET /", "GET /static/*", "GET /api/simulate", "GET /api/benchmark"],
        "fields": ["all response fields and path parameters"],
        "date_or_population": "Adversarial local requests"
      },
      "prerequisites": ["SCEN-004", "SEC-001"],
      "procedure": [
        "Enumerate routes and response schemas.",
        "Attempt encoded traversal, unknown paths, malformed queries, and error-triggering inputs.",
        "Search response bodies for raw records, filesystem paths, stack traces, or excessive segment detail."
      ],
      "suggested_commands": ["Use localhost requests against an isolated local server or mock handler."],
      "assertions": ["Only intended static files and aggregate outputs are returned.", "Errors do not expose local state or raw data."],
      "reconciliation": {
        "source_measure": "declared endpoint contracts",
        "target_measure": "observed responses",
        "grain": "request",
        "tolerance": "0 unauthorized disclosures"
      },
      "evidence_required": ["Route inventory", "request/response status table", "redacted disclosure samples"],
      "completion_criteria": ["Every route and traversal/error class has a result."],
      "possible_issue_fingerprints": ["exposure:path-traversal", "exposure:api-raw-data:<endpoint>", "exposure:stack-trace:<endpoint>"],
      "estimated_effort": "medium"
    },
    {
      "id": "SEC-003",
      "domain": "U. Restricted-data and exposure review",
      "title": "Audit reports, logs, caches, and serialized artifacts for exposure",
      "priority": "P1",
      "objective": "Do PDFs, figures, logs, caches, or pickle contents contain restricted rows, quasi-identifiers, or unnecessary detail?",
      "risk": "Exposure may occur outside the web surface.",
      "scope": {
        "files": ["output/**/*", "tmp/**/*", "__pycache__/**/*", ".pytest_cache/**/*", "lake/curated/residual_engine.pkl", "DATA_ISSUES.pdf"],
        "tables_or_sheets": ["ALL"],
        "fields": ["embedded text, metadata, row samples, paths"],
        "date_or_population": "ALL discovered generated artifacts"
      },
      "prerequisites": ["INV-001", "SEC-001"],
      "procedure": [
        "Extract report text and metadata and inspect figure labels.",
        "Inspect cache strings and pickle metadata in isolation.",
        "Search for raw headers, exact row fingerprints, usernames, and absolute paths."
      ],
      "suggested_commands": ["pdftotext <pdf> -; strings <artifact> with targeted patterns; python -m pickletools <pkl>"],
      "assertions": ["Generated artifacts contain only necessary aggregate evidence.", "No material PII or quasi-identifying combination is exposed."],
      "reconciliation": {
        "source_measure": "restricted fingerprints and sensitive patterns",
        "target_measure": "generated-artifact matches",
        "grain": "artifact/match",
        "tolerance": "0 unauthorized matches"
      },
      "evidence_required": ["Artifact scan inventory", "redacted matches", "metadata findings"],
      "completion_criteria": ["Every generated, cached, and serialized artifact is scanned."],
      "possible_issue_fingerprints": ["exposure:report-raw-row:<path>", "exposure:absolute-path:<path>", "exposure:sensitive-cache:<path>"],
      "estimated_effort": "medium"
    },
    {
      "id": "DOC-001",
      "domain": "V. Documentation gaps and unsupported claims",
      "title": "Classify every material implementation and performance claim",
      "priority": "P1",
      "objective": "Which claims are reproduced, inspected, merely claimed, or missing/contradicted?",
      "risk": "Unsupported statements can overstate readiness and model validity.",
      "scope": {
        "files": ["README.md", "docs/*.md", "src/app/static/index.html", "output/**/*"],
        "tables_or_sheets": ["NOT_APPLICABLE"],
        "fields": ["all material data, modelling, uncertainty, simulator, and test claims"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["CONS-001", "CONS-002", "CONS-003", "TEST-001"],
      "procedure": [
        "Extract atomic factual claims with citations.",
        "Link each to reproduced or inspected evidence from prior tasks.",
        "Assign exactly one evidence class and record contradictions."
      ],
      "suggested_commands": ["Search declarative metrics and capability language; use prior task evidence rather than rerunning transformations."],
      "assertions": ["Every material claim has one evidence classification.", "Passing tests or file existence are not treated as proof of statistical validity."],
      "reconciliation": {
        "source_measure": "material claims",
        "target_measure": "classified claims",
        "grain": "claim",
        "tolerance": "100% coverage"
      },
      "evidence_required": ["Claim register", "citations", "linked task evidence", "classification rationale"],
      "completion_criteria": ["No material claim remains unclassified."],
      "possible_issue_fingerprints": ["claim:unsupported:<semantic-signature>", "claim:contradicted:<semantic-signature>", "claim:evidence-overstated:<semantic-signature>"],
      "estimated_effort": "large"
    },
    {
      "id": "DOC-002",
      "domain": "V. Documentation gaps and unsupported claims",
      "title": "Audit causal language, precision, and assumption labeling",
      "priority": "P0",
      "objective": "Are observational relationships, effective multipliers, assumptions, estimates, overrides, and uncertainty described honestly?",
      "risk": "Unsupported causal or observed-fact language can materially mislead policy decisions.",
      "scope": {
        "files": ["README.md", "docs/*.md", "src/app/**/*", "output/**/*"],
        "tables_or_sheets": ["NOT_APPLICABLE"],
        "fields": ["causal verbs", "confidence/calibrated language", "observed/estimated/assumed labels", "numeric precision"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["BRG-002", "UNC-002", "DOC-001"],
      "procedure": [
        "Search for causal, calibrated, measured, exact, confidence, and certainty language.",
        "Compare each phrase with the available evidence and estimand.",
        "Check that displayed precision does not exceed source or validation support."
      ],
      "suggested_commands": ["rg -ni 'cause|impact|drives|measured|observed|calibrated|confidence|exact|guarantee|predicts' README.md docs app"],
      "assertions": ["Aggregate observational estimates are not presented as causal effects.", "Assumptions and planner overrides are distinguishable from observations.", "Coverage shortfalls remain visible."],
      "reconciliation": {
        "source_measure": "claim wording",
        "target_measure": "evidentiary support",
        "grain": "claim",
        "tolerance": "semantic support required"
      },
      "evidence_required": ["Phrase citations", "support comparison", "precision examples"],
      "completion_criteria": ["Every high-risk phrase has a supported or contradicted verdict."],
      "possible_issue_fingerprints": ["claim:unsupported-causal-language:<surface>", "claim:assumption-as-observed:<surface>", "claim:false-calibration:<surface>", "claim:false-precision:<surface>"],
      "estimated_effort": "medium"
    },
    {
      "id": "DOC-003",
      "domain": "V. Documentation gaps and unsupported claims",
      "title": "Identify stale guidance and required owner decisions",
      "priority": "P2",
      "objective": "Which schemas, commands, screenshots, counts, limitations, and business meanings are stale, absent, or require owner confirmation?",
      "risk": "Users may execute wrong steps or interpret unresolved semantics as settled.",
      "scope": {
        "files": ["README.md", "docs/*.md", "Makefile", "requirements.txt", "src/app/**/*", "output/**/*"],
        "tables_or_sheets": ["NOT_APPLICABLE"],
        "fields": ["commands", "paths", "schema", "counts", "screenshots", "limitations", "business definitions"],
        "date_or_population": "ALL"
      },
      "prerequisites": ["INV-003", "RAW-003", "DOC-001"],
      "procedure": [
        "Test documented local commands in the isolated rebuild environment.",
        "Compare schemas, counts, UI descriptions, and limitations with current behavior.",
        "Create a finite owner-question register for unresolved material meanings and thresholds."
      ],
      "suggested_commands": ["Validate commands with --help or isolated execution; compare cited paths with inventory."],
      "assertions": ["Instructions match current repository behavior.", "Unknown business semantics are explicitly posed as owner questions."],
      "reconciliation": {
        "source_measure": "documented commands and facts",
        "target_measure": "observed current behavior",
        "grain": "instruction/claim",
        "tolerance": "exact for commands, paths, schemas, and counts"
      },
      "evidence_required": ["Stale-item list", "command results", "owner-question register with affected decisions"],
      "completion_criteria": ["Every documentation mismatch and material unknown is recorded."],
      "possible_issue_fingerprints": ["docs:stale-command:<command>", "docs:stale-schema:<artifact>", "docs:missing-limitation:<risk>", "owner-question:<semantic-topic>"],
      "estimated_effort": "medium"
    },
    {
      "id": "VS-001",
      "domain": "W. Vertical-slice audits",
      "title": "Trace a high-volume international market",
      "priority": "P0",
      "objective": "Can one high-volume market, selected by training guest volume, be traced from raw records to UI without unexplained loss or semantic change?",
      "risk": "A defect in a dominant market materially affects headline totals.",
      "scope": {
        "files": ["01a - DCT Dataset/*", "lake/**/*", "scripts/*.py", "src/engine/*.py", "src/app/**/*"],
        "tables_or_sheets": ["ALL lifecycle stages"],
        "fields": ["keys, units, statuses, mappings, parameters, outputs"],
        "date_or_population": "Highest-volume international market with one complete holdout week"
      },
      "prerequisites": ["REC-007", "CAT-002", "LEAK-002"],
      "procedure": [
        "Select the market reproducibly from training-only guest volume.",
        "Trace raw rows through parsing, daily curation, weekly aggregation, model input, calibration/inference, scenario, API, and UI.",
        "At every transition record keys, grain, units, flags, filters, assumptions, and reconciliation."
      ],
      "suggested_commands": ["Use read-only keyed queries and one deterministic no-change plus positive-capacity scenario."],
      "assertions": ["Every transition reconciles.", "No realized holdout value enters planning inference."],
      "reconciliation": {
        "source_measure": "stage input records and totals",
        "target_measure": "next-stage records and totals",
        "grain": "selected market/week/stage",
        "tolerance": "exact except documented display rounding"
      },
      "evidence_required": ["Complete trace packet", "queries", "file:line citations", "stage exceptions"],
      "completion_criteria": ["All lifecycle stages are evidenced for one reproducibly selected high-volume market."],
      "possible_issue_fingerprints": ["vertical:high-volume:<stage>:<field>", "vertical:high-volume:unreconciled:<transition>"],
      "estimated_effort": "large"
    },
    {
      "id": "VS-002",
      "domain": "W. Vertical-slice audits",
      "title": "Trace a sparse international market",
      "priority": "P1",
      "objective": "How does the full system behave for the supported international market with the fewest eligible training weeks or volume?",
      "risk": "Sparse estimates may appear as precise as well-supported markets.",
      "scope": {
        "files": ["01a - DCT Dataset/*", "lake/**/*", "scripts/*.py", "src/engine/*.py", "src/app/**/*"],
        "tables_or_sheets": ["ALL lifecycle stages"],
        "fields": ["historical_weeks", "parameters", "fallbacks", "uncertainty", "outputs"],
        "date_or_population": "Reproducibly selected sparse supported market and one complete week"
      },
      "prerequisites": ["VS-001", "STAT-002", "UNC-004"],
      "procedure": [
        "Select the sparsest supported market using a prespecified training-only rule.",
        "Trace the same lifecycle transitions as VS-001.",
        "Emphasize support counts, parameter stability, fallbacks, interval width, and UI disclosure."
      ],
      "suggested_commands": ["Use read-only queries and deterministic scenarios."],
      "assertions": ["Sparse support is visible.", "No hidden generic fallback is presented as market-specific evidence."],
      "reconciliation": {
        "source_measure": "stage inputs",
        "target_measure": "stage outputs",
        "grain": "selected market/week/stage",
        "tolerance": "exact except documented display rounding"
      },
      "evidence_required": ["Complete trace packet", "support counts", "uncertainty comparison", "exceptions"],
      "completion_criteria": ["Every lifecycle transition and support-sensitive behavior is evidenced."],
      "possible_issue_fingerprints": ["vertical:sparse:<stage>:<field>", "vertical:sparse:false-precision", "vertical:sparse:hidden-fallback"],
      "estimated_effort": "large"
    },
    {
      "id": "VS-003",
      "domain": "W. Vertical-slice audits",
      "title": "Trace a hub-mediated or indirect-travel market",
      "priority": "P0",
      "objective": "How does a hub-mediated market traverse the same-label bridge despite indirect or connecting travel risk?",
      "risk": "Departure-country proxies are weakest where travelers arrive through other hubs.",
      "scope": {
        "files": ["01a - DCT Dataset/*", "lake/**/*", "src/engine/archetypes.py", "src/engine/panel.py", "src/engine/structural.py", "src/app/**/*"],
        "tables_or_sheets": ["ALL lifecycle stages"],
        "fields": ["departure_country_name", "nationality", "transfer", "transit", "p2p", "effective_response_multiplier"],
        "date_or_population": "One supported Hub-Mediated market and one complete holdout week"
      },
      "prerequisites": ["BRG-001", "BRG-004", "REC-007"],
      "procedure": [
        "Select a Hub-Mediated market deterministically from MARKET_ARCHETYPE_MAP.",
        "Trace origin and nationality populations separately before panel matching.",
        "Record indirect-travel assumptions and sensitivity through API/UI output."
      ],
      "suggested_commands": ["Use keyed source and panel queries plus current and alternative bridge scenarios."],
      "assertions": ["Origin and nationality remain separately evidenced.", "Indirect-travel limitations are visible in interpretation."],
      "reconciliation": {
        "source_measure": "origin-domain and nationality-domain stage inputs",
        "target_measure": "panel, parameter, and scenario outputs",
        "grain": "market/week/stage",
        "tolerance": "exact accounting; bridge sensitivity reported"
      },
      "evidence_required": ["Dual-domain trace", "bridge assumption record", "sensitivity results", "surface labels"],
      "completion_criteria": ["Every transition and indirect-travel assumption is evidenced."],
      "possible_issue_fingerprints": ["vertical:hub-mediated:entity-conflation", "vertical:hub-mediated:bridge-sensitive", "vertical:hub-mediated:limitation-hidden"],
      "estimated_effort": "large"
    },
    {
      "id": "VS-004",
      "domain": "W. Vertical-slice audits",
      "title": "Trace pooled OTHER INTERNATIONAL populations",
      "priority": "P0",
      "objective": "Do legacy OTHER, catch-all OTHER_INTERNATIONAL, and regional clusters preserve members, totals, parameters, and runtime compatibility?",
      "risk": "Pooled populations can be omitted, duplicated, or loaded from stale artifacts.",
      "scope": {
        "files": ["01a - DCT Dataset/*", "src/engine/archetypes.py", "src/engine/panel.py", "lake/**/*", "src/app/**/*"],
        "tables_or_sheets": ["ALL lifecycle stages"],
        "fields": ["nationality", "departure_country_name", "market", "archetype", "parameters", "model keys"],
        "date_or_population": "All pooled-member categories for one complete week and all artifacts"
      },
      "prerequisites": ["AGG-003", "REC-007"],
      "procedure": [
        "Trace each pooled member from both source domains into its current cluster.",
        "Reconcile union totals and detect overlap.",
        "Trace cluster or legacy keys through calibration, residual model, simulator, API, and UI."
      ],
      "suggested_commands": ["Use read-only membership joins and deterministic scenarios for each pooled label."],
      "assertions": ["Each member appears exactly once.", "Artifact keys and runtime keys are compatible or visibly fall back."],
      "reconciliation": {
        "source_measure": "member-category rows and totals",
        "target_measure": "pooled lifecycle outputs",
        "grain": "member/week/stage",
        "tolerance": "exact"
      },
      "evidence_required": ["Membership trace", "union reconciliation", "artifact key comparison", "fallback samples"],
      "completion_criteria": ["Every pooled member and label is traced end to end."],
      "possible_issue_fingerprints": ["vertical:other:member-loss:<value>", "vertical:other:member-double:<value>", "vertical:other:artifact-key-mismatch:<label>"],
      "estimated_effort": "large"
    },
    {
      "id": "VS-005",
      "domain": "W. Vertical-slice audits",
      "title": "Trace DOMESTIC demand end to end",
      "priority": "P0",
      "objective": "Is domestic staycation demand kept separate from international aviation inputs and metrics at every stage?",
      "risk": "Domestic volume can contaminate aviation interpretation and headline performance.",
      "scope": {
        "files": ["01a - DCT Dataset/data domestic_*.xlsx", "lake/**/*", "src/engine/*.py", "scripts/evaluate_models.py", "src/app/**/*"],
        "tables_or_sheets": ["ALL lifecycle stages"],
        "fields": ["residence_group", "market", "is_domestic", "guests", "domestic priors", "aviation fields"],
        "date_or_population": "One complete domestic holdout week and all domestic evaluation rows"
      },
      "prerequisites": ["SCEN-001", "MET-003", "REC-007"],
      "procedure": [
        "Trace a domestic raw date through curated, weekly, model, evaluation, scenario, API, and UI layers.",
        "Verify flight measures and flight levers are inactive.",
        "Reconcile domestic metrics separately and measure contribution to combined metrics."
      ],
      "suggested_commands": ["Use read-only queries and domestic scenarios with every aviation lever."],
      "assertions": ["Domestic demand has no unjustified international flight dependence.", "Domestic and combined metrics are distinctly labeled."],
      "reconciliation": {
        "source_measure": "domestic raw and curated guest values",
        "target_measure": "domestic panel, model, evaluation, and scenario outputs",
        "grain": "week/stage",
        "tolerance": "exact except documented display rounding"
      },
      "evidence_required": ["Complete trace", "lever-invariance matrix", "metric contribution"],
      "completion_criteria": ["Domestic separation is evidenced at every lifecycle stage."],
      "possible_issue_fingerprints": ["vertical:domestic:aviation-coupling", "vertical:domestic:metric-conflation", "vertical:domestic:unit-mismatch"],
      "estimated_effort": "large"
    },
    {
      "id": "VS-006",
      "domain": "W. Vertical-slice audits",
      "title": "Trace an unsupported cold-start market",
      "priority": "P1",
      "objective": "What happens from an unknown market request through fallback parameters, uncertainty, API, and UI?",
      "risk": "Unsupported markets may receive unjustifiably precise estimates.",
      "scope": {
        "files": ["src/engine/archetypes.py", "src/engine/structural.py", "src/engine/uncertainty.py", "src/engine/simulator.py", "src/app/**/*"],
        "tables_or_sheets": ["GET /api/simulate"],
        "fields": ["market", "archetype", "is_cold_start", "historical_weeks", "fallback parameters", "uncertainty"],
        "date_or_population": "One mapped-but-uncalibrated country and one completely unknown label"
      },
      "prerequisites": ["BRG-003", "UNC-004", "SCEN-004"],
      "procedure": [
        "Select both cold-start cases with no calibration artifact entry.",
        "Trace fallback selection and all scenario fields.",
        "Compare interval width, warning, recommendation, API, and UI with a supported peer."
      ],
      "suggested_commands": ["Use deterministic direct-engine and API calls."],
      "assertions": ["is_cold_start is true and visible.", "Fallback provenance is deterministic.", "Unsupported estimates do not masquerade as locally calibrated."],
      "reconciliation": {
        "source_measure": "archetype fallback defaults",
        "target_measure": "runtime parameters and outputs",
        "grain": "market/season/field",
        "tolerance": "exact"
      },
      "evidence_required": ["Fallback trace", "supported-peer comparison", "API/UI disclosure evidence"],
      "completion_criteria": ["Both regional and generic fallback routes are fully traced."],
      "possible_issue_fingerprints": ["vertical:cold-start:false-supported-label", "vertical:cold-start:fallback-mismatch", "vertical:cold-start:false-precision"],
      "estimated_effort": "medium"
    },
    {
      "id": "VS-007",
      "domain": "W. Vertical-slice audits",
      "title": "Trace a split-boundary period",
      "priority": "P0",
      "objective": "Does a week near the 2024-12-30 training/holdout boundary remain complete, unique, and leakage-free through evaluation?",
      "risk": "Boundary contamination directly invalidates forward-holdout claims.",
      "scope": {
        "files": ["01a - DCT Dataset/*", "lake/**/*", "src/engine/panel.py", "scripts/train_models.py", "scripts/evaluate_models.py"],
        "tables_or_sheets": ["ALL data and model stages"],
        "fields": ["date", "week_start", "dataset_split", "days_in_week", "is_complete_week", "model role"],
        "date_or_population": "Weeks immediately before, containing, and after 2024-12-30"
      },
      "prerequisites": ["TEMP-003", "LEAK-001", "REC-006"],
      "procedure": [
        "Trace every contributing date and market row across the boundary.",
        "Verify no week or daily flight total is duplicated across split-specific guest rows.",
        "Confirm fitting, calibration, and evaluation roles."
      ],
      "suggested_commands": ["Use read-only date-range queries and row-key set comparisons."],
      "assertions": ["Boundary weeks have correct dates and one role.", "No future row influences training parameters or preprocessing."],
      "reconciliation": {
        "source_measure": "boundary daily rows",
        "target_measure": "weekly rows and role membership",
        "grain": "date/week_start/market",
        "tolerance": "exact"
      },
      "evidence_required": ["Boundary date trace", "weekly totals", "role-set evidence", "exceptions"],
      "completion_criteria": ["All dates and markets in the boundary window are accounted for."],
      "possible_issue_fingerprints": ["vertical:boundary:split-overlap:<key>", "vertical:boundary:flight-duplication:<week>", "vertical:boundary:future-fit:<operation>"],
      "estimated_effort": "large"
    },
    {
      "id": "VS-008",
      "domain": "W. Vertical-slice audits",
      "title": "Trace a missing or suppressed source period",
      "priority": "P0",
      "objective": "Are missing, absent, and suppressed observations preserved and prevented from becoming complete zero-valued model inputs?",
      "risk": "Status collapse can fabricate demand declines or false complete periods.",
      "scope": {
        "files": ["01a - DCT Dataset/data *.xlsx", "scripts/build_lake.py", "lake/**/*", "src/engine/panel.py", "scripts/*.py", "src/app/**/*"],
        "tables_or_sheets": ["ALL lifecycle stages"],
        "fields": ["source markers", "is_source_present", "suppression flags", "missing_arrival_records", "is_complete_guest_inputs", "targets"],
        "date_or_population": "One reproducibly selected missing-row case and one suppressed-value case"
      },
      "prerequisites": ["MISS-002", "MISS-003", "REC-004"],
      "procedure": [
        "Select cases from raw evidence without assuming they are defects.",
        "Trace marker and row status through curated, weekly, model-population, evaluation, scenario, API, and UI layers.",
        "Verify incomplete data are excluded or visibly qualified."
      ],
      "suggested_commands": ["Use read-only keyed queries beginning from exact raw cell coordinates."],
      "assertions": ["Status semantics survive every transition.", "Missing or suppressed observations are not silently treated as genuine zero or complete input."],
      "reconciliation": {
        "source_measure": "raw status and value",
        "target_measure": "downstream flags, inclusion, and displayed behavior",
        "grain": "selected row/week/stage",
        "tolerance": "exact status lineage"
      },
      "evidence_required": ["Raw cell coordinates", "complete status trace", "population inclusion evidence", "surface behavior"],
      "completion_criteria": ["Both missing-row and suppressed-value cases are traced through every applicable stage."],
      "possible_issue_fingerprints": ["vertical:missing:status-lost:<stage>", "vertical:missing:treated-zero:<stage>", "vertical:suppressed:treated-complete:<stage>"],
      "estimated_effort": "large"
    }
  ],
  "final_completeness_checks": [
    "Every required domain A-W has at least one task.",
    "Every source and curated asset is covered.",
    "Every major transformation has source-to-target reconciliation.",
    "Every published headline claim has a consistency task.",
    "At least one task covers each evidence class and major semantic distinction.",
    "No task writes to DATA_ISSUES_GEMMA.md.",
    "Every prerequisite ID resolves to a task in this checklist.",
    "Every execution-order task ID resolves to a task in this checklist.",
    "Every task appears exactly once in execution_order.",
    "Raw departure country and hotel-guest nationality are never assumed equivalent.",
    "Observed, derived, assumed, imputed, model-estimated, and planner-override values are explicitly distinguished.",
    "Planning-time and realized variables are separately audited.",
    "Point forecasts, empirical coverage, interval width, and uncertainty estimands are separately audited.",
    "Domestic staycation and international aviation-driven demand are separately audited.",
    "Absent, zero, suppressed, unavailable, and not-applicable states are separately audited.",
    "Every reconciliation requires both aggregate controls and record-level exceptions where applicable.",
    "Every unknown business threshold requires distribution evidence and owner confirmation rather than an invented cutoff.",
    "All suggested execution is local, read-only, and requires no external service.",
    "The checklist is finite: it contains 89 bounded tasks.",
    "The JSON object is syntactically valid."
  ]
}
