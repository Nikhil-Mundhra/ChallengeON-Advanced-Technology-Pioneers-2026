# Local agentic data-audit loop

The controller parses the checklist locally and sends one bounded task at a time to
the configured finder. It owns scheduling, retries, issue deduplication, durable
state, and Markdown rendering. No model receives the complete checklist or issue
register.

Before scheduling work, the controller builds a deterministic repository map under
`audit/discovery/`. The filename contains a fingerprint derived from source contents
and structured-asset metadata, so unchanged repositories reuse the same version.
Each finder receives only its scoped files, top-level Python symbols and imports,
related tests/modules, and matching data assets. This context is navigation metadata,
not audit evidence; material claims must still be reproduced with read-only tools.

Start the local Qwen server in non-thinking mode. Keeping this setting at the
server boundary also allows its prompt cache to be reused:

```bash
mlx_lm.server \
  --model mlx-community/Qwen3.5-4B-MLX-4bit \
  --port 8000 \
  --max-tokens 8192 \
  --prefill-step-size 256 \
  --chat-template-args '{"enable_thinking": false}'
```

The audit client defaults to `http://localhost:8000/v1/chat/completions` and disables
thinking in each request. Investigation turns are capped at 1,024 output tokens. Once
the finder returns `ready_to_finalize`, a dedicated streamed final-report request gets
up to 8,192 tokens and a 15-minute total deadline with inactivity protection. Override
these independently with `--local-max-tokens` and `--local-final-max-tokens`.
Tool results are retained at up to 8,000 serialized characters each and local prompt
history is compacted above 280,000 characters, keeping long investigations well below
the model's theoretical context ceiling. These guardrails matter on macOS even when
the KV cache fits in unified memory: a very long prefill can trigger Metal's
`Impacting Interactivity` watchdog. Override them with `--local-tool-result-chars`
and `--local-max-prompt-chars` only after measuring the host.

Initialize and inspect the queue:

```bash
.venv/bin/python scripts/run_data_issues_audit.py init
.venv/bin/python scripts/run_data_issues_audit.py status
```

Watch the live terminal dashboard (Ctrl+C stops only the dashboard, not the audit):

```bash
.venv/bin/python scripts/run_data_issues_audit.py watch
```

The refresh interval defaults to two seconds and can be changed with
`--watch-interval`. Use `status --json` for a machine-readable snapshot or
`watch --json` for newline-delimited snapshots.

Run one task for a controlled test:

```bash
.venv/bin/python scripts/run_data_issues_audit.py run --max-tasks 1
```

Run until the finite checklist is exhausted:

```bash
.venv/bin/python scripts/run_data_issues_audit.py run --max-tasks 0
```

Run OpenCode as the primary finder. Each task gets a fresh isolated OpenCode session;
if every configured model fails, the controller falls back to local Qwen by default.
The issue-manager step also uses local Qwen:

```bash
.venv/bin/python scripts/run_data_issues_audit.py run --max-tasks 0 --with-opencode
```

For an OpenCode-only finder run with no local Qwen fallback:

```bash
.venv/bin/python scripts/run_data_issues_audit.py run --max-tasks 0 \
  --finder-backend opencode --no-local-fallback
```

Use `--finder-backend qwen --with-opencode` only when you explicitly want a
Qwen-first, OpenCode-on-blocker run.

To escalate terminal tasks from an earlier local-model run, first ensure no audit task
is currently running, then execute:

```bash
.venv/bin/python scripts/run_data_issues_audit.py escalate --max-tasks 0
```

OpenCode escalation sessions are read-only and stored under `audit/escalations/`.
They establish audit findings and evidence; they do not repair production code or data.
Each escalation runs in an isolated temporary OpenCode workspace by default. Only the
minimal audit agent definition is loaded up front; the repository root is supplied
explicitly and inspected on demand. This avoids preloading project/global skills and
workspace configuration into every model turn. External plugins, Claude-compatible
instructions, and project configuration discovery are disabled for the subprocess.
Each model streams raw events to `<model>.events.jsonl` and updates `progress.json`
every five seconds. Progress distinguishes unique completed tool calls from narration,
tracks repeated calls, detects a verdict candidate, and records the last action. By
default a model is stopped after 10 minutes without a new unique tool result or
verdict, after 30 completed tool calls, after four identical consecutive calls, or
after the 30-minute absolute timeout. These limits can be adjusted with
`--escalation-stall-timeout`, `--escalation-max-tool-calls`,
`--escalation-max-repeat`, and `--escalation-timeout`.

## Observed 32 GB Mac memory envelope

The following is the measured operating baseline for this audit, not a theoretical
model-size estimate:

| Component | Current memory |
| --- | ---: |
| Qwen MLX server | ~17.0 GB physical footprint |
| Vivaldi | ~2.70 GB RSS |
| ChatGPT/Codex | ~1.95 GB RSS |
| OpenCode worker | ~0.88 GB RSS |
| JetBrains Toolbox | ~0.25 GB RSS |
| Box + Google Drive | ~0.37 GB RSS |
| Audit controller | ~0.04 GB RSS |
| macOS and remaining processes | ~4.70 GB RSS |

Run only one local model server. Treat memory pressure and swap as the operational
signals; do not infer available headroom solely from the model weight file size.

The normal status command includes any active escalation telemetry:

```bash
.venv/bin/python scripts/run_data_issues_audit.py status
```

To recover or rerun one earlier terminal escalation without processing every older
terminal task:

```bash
.venv/bin/python scripts/run_data_issues_audit.py escalate --task-id KEY-003
```

Existing model output is checked for a valid embedded verdict before a new remote
request is started, so narration before the JSON does not discard a usable result.

Reset a terminal or failed task when its limitation has been corrected:

```bash
.venv/bin/python scripts/run_data_issues_audit.py retry --task-id INV-001
```

For an infrastructure-only attempt that must not consume a retry, add
`--undo-attempt`. Use `--retry-status pending` when restoring a task that had not
actually started before the failed controller launch. The command also clears stale
timestamps, backend ownership, escalation metadata, and controller PID.

Canonical state is stored beneath `audit/`. `DATA_ISSUES_GEMMA.md` is a generated
view of `audit/issues.json` and should not be edited directly. Finder transcripts,
task reports, and manager decisions are retained separately for auditability.
