# Local agentic data-audit loop

Driven by `scripts/run_data_issues_audit.py`. The controller parses the checklist
(`DATA_ISSUES_CHECKLIST.md` by default) locally and sends one bounded task at a time to
the configured finder. It owns scheduling, retries, issue deduplication, durable state,
and Markdown rendering. No model receives the complete checklist or issue register.

Before scheduling, the controller builds a deterministic repository map in
`audit/discovery/`: `repository_map.json` plus a copy named
`repository_map.<fingerprint>.json`, where the fingerprint covers source contents and
data-asset metadata, so an unchanged repository reuses the same map. Each finder
receives only its scoped files, top-level Python symbols and imports, related
tests/modules, and matching data assets. This is navigation metadata, not audit
evidence: material claims must be reproduced with read-only tools.

## Local Qwen server

Run in non-thinking mode; setting it at the server also lets the prompt cache be reused:

```bash
mlx_lm.server \
  --model mlx-community/Qwen3.5-4B-MLX-4bit \
  --port 8000 \
  --max-tokens 8192 \
  --prefill-step-size 256 \
  --chat-template-args '{"enable_thinking": false}'
```

| Client setting | Default | Flag |
| --- | --- | --- |
| Endpoint | `http://localhost:8000/v1/chat/completions` | `--endpoint` |
| Model | `mlx-community/Qwen3.5-4B-MLX-4bit` | `--model` |
| Output tokens per investigation turn | 1,024 | `--local-max-tokens` |
| Output tokens for the final report (streamed, 15-minute deadline, inactivity protection) | 8,192 | `--local-final-max-tokens` |
| Retained characters per tool result | 8,000 | `--local-tool-result-chars` |
| Prompt history compacted above (characters) | 280,000 | `--local-max-prompt-chars` |

Thinking is also disabled in each request. The prompt limits keep prefill short: on
macOS a very long prefill can trigger Metal's `Impacting Interactivity` watchdog even
when the KV cache fits in unified memory. Raise them only after measuring the host.

## Commands

```bash
.venv/bin/python scripts/run_data_issues_audit.py init      # create the task queue
.venv/bin/python scripts/run_data_issues_audit.py status    # snapshot, incl. active escalation telemetry (--json)
.venv/bin/python scripts/run_data_issues_audit.py watch     # live dashboard; Ctrl+C stops only the dashboard
                                                            # (--watch-interval, default 2 s; --json for NDJSON)
.venv/bin/python scripts/run_data_issues_audit.py run --max-tasks 1   # one task (default)
.venv/bin/python scripts/run_data_issues_audit.py run --max-tasks 0   # until the checklist is exhausted
```

### Finder backends

| Command | Finder | Fallback |
| --- | --- | --- |
| `run --max-tasks 0` | local Qwen | — |
| `run --max-tasks 0 --with-opencode` | OpenCode (fresh isolated session per task) | local Qwen if every OpenCode model fails |
| `run --max-tasks 0 --finder-backend opencode --no-local-fallback` | OpenCode | none |
| `run --finder-backend qwen --with-opencode` | local Qwen | OpenCode on blocker |

The issue-manager step always uses local Qwen.

### Escalation

Re-run terminal tasks from an earlier local-model run with OpenCode. Ensure no audit
task is running first.

```bash
.venv/bin/python scripts/run_data_issues_audit.py escalate --max-tasks 0
.venv/bin/python scripts/run_data_issues_audit.py escalate --task-id KEY-003   # one task
```

- Sessions are read-only, stored under `audit/escalations/`, and establish findings and
  evidence; they do not repair code or data.
- Each runs in an isolated temporary OpenCode workspace with only the minimal audit
  agent definition loaded; the repository root is passed explicitly and read on demand.
  External plugins (unless `--opencode-with-plugins`), Claude-compatible instructions,
  and project configuration discovery are disabled.
- Each model streams raw events to `<model>.events.jsonl` and updates `progress.json`
  every 5 seconds (unique completed tool calls, repeated calls, verdict candidate, last
  action).
- Existing model output is checked for a valid embedded verdict before a new request is
  started, so narration before the JSON does not discard a usable result.

| Stop condition | Default | Flag |
| --- | --- | --- |
| No new unique tool result or verdict | 10 min | `--escalation-stall-timeout` (seconds) |
| Completed tool calls | 30 | `--escalation-max-tool-calls` |
| Identical consecutive calls | 4 (3 repeats) | `--escalation-max-repeat` |
| Absolute timeout | 30 min | `--escalation-timeout` (seconds) |

### Retry

Reset a terminal or failed task after its limitation is fixed:

```bash
.venv/bin/python scripts/run_data_issues_audit.py retry --task-id INV-001
```

`--undo-attempt` does not consume a retry (for infrastructure failures);
`--retry-status pending` restores a task that never started. Retry also clears stale
timestamps, backend ownership, escalation metadata, and controller PID.

## State

Canonical state is under `audit/` (gitignored). `DATA_ISSUES_GEMMA.md` (`--output`) is
generated from `audit/issues.json`; do not edit it. Finder transcripts, task reports,
and manager decisions are kept separately.

## Observed memory on a 32 GB Mac

Measured during this audit:

| Component | Memory |
| --- | ---: |
| Qwen MLX server | ~17.0 GB physical footprint |
| Vivaldi | ~2.70 GB RSS |
| ChatGPT/Codex | ~1.95 GB RSS |
| OpenCode worker | ~0.88 GB RSS |
| JetBrains Toolbox | ~0.25 GB RSS |
| Box + Google Drive | ~0.37 GB RSS |
| Audit controller | ~0.04 GB RSS |
| macOS and remaining processes | ~4.70 GB RSS |

Run one local model server at a time. Use memory pressure and swap, not the model
weight file size, to judge headroom.
