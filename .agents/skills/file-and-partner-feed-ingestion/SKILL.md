---
name: file-and-partner-feed-ingestion
description: Guides agents through file-based and partner-feed ingestion workflows. Use when landing data from SFTP, managed file transfer, shared buckets, recurring flat files, manifests, or externally supplied feeds that need validation, replay safety, and publish discipline.
---

# File And Partner Feed Ingestion

## When to Use

- Onboarding SFTP, MFT, or shared-bucket feeds.
- Ingesting recurring CSV/JSON/XML/columnar extracts from external partners.
- Validating manifests, checksums, control totals, or arrival windows.
- Handling late, duplicate, partial, or corrected deliveries.

Do not assume batch file delivery is simple.

## In this repo

- Raw source: organizer-supplied workbooks in `01a - DCT Dataset/` (or `TWIN_SOURCE_DIR`); never edit or commit them.
- Ingest via `twin build-lake` (`data/ingest.py` → `validation.py` → `lake_writer.py` → `manifest.py`); rebuild into a scratch `TWIN_LAKE_DIR` to avoid overwriting committed artifacts.

## Workflow

1. Define the feed contract: format and schema, naming, arrival schedule/SLA, manifest/checksum/control totals, partner owner and contact.
2. Design landing: raw location, captured metadata, duplicate detection, quarantine for partial or corrupt files.
3. Validate before publish: schema and required fields, checksum/manifest, row counts/control totals, late or missing files.
4. Make replay explicit: corrected files, duplicates ignored or reconciled, bounded replay windows, downstream publish blocked until validation passes.
5. Define failure handling: who is alerted, what blocks publish, how the partner is contacted, how recovery evidence is recorded.

## Red Flags

- Validation deferred until after loading.
- Resends handled without replay safety (duplicate or conflicting publishes).
- Naming and arrival expectations undocumented.
- Manifests, checksums, or control totals ignored.
- Duplicate and corrected-file behavior undefined.
- Late or missing files raise no actionable alert.
- Downstream publish opens before landing validation completes.

## Verification

- [ ] The feed contract defines format, arrival, and ownership
- [ ] Landing, quarantine, and duplicate handling are explicit
- [ ] Validation covers schema, completeness, and control totals
- [ ] Replay and corrected-file behavior are documented before go-live
- [ ] Failure handling and partner escalation are defined
