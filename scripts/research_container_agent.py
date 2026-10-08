"""Resumable, memory-capped research controller using the host macOS MLX server.

Only the controller is in Docker. The host MLX process is outside its cgroup.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import urllib.request
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from research_real_world import OUT, SYSTEM, data, fetch, search

MODEL = "mlx-community/Qwen3.5-4B-MLX-4bit"
API = "http://host.docker.internal:8000/v1/chat/completions"
STEP_LOG = OUT / "container_steps.jsonl"
MEMORY = OUT / "memory.md"
NEXT = OUT / "next_prompt.md"
INDEX = OUT / "memory_index.sqlite"
MODEL_SUMMARIES = OUT / "model_compactions.md"
WARN_BYTES = 700 * 1024**2
STOP_BYTES = 850 * 1024**2
MAX_PROMPT_CHARS = 12_000


def cgroup_bytes() -> int:
    for path in ("/sys/fs/cgroup/memory.current", "/sys/fs/cgroup/memory/memory.usage_in_bytes"):
        try:
            return int(Path(path).read_text().strip())
        except (OSError, ValueError):
            continue
    raise RuntimeError("Container memory cgroup unavailable; refusing uncapped run")


def chat(messages: list[dict], max_tokens: int = 400) -> str:
    payload = {"model": MODEL, "messages": messages, "stream": False,
               "chat_template_kwargs": {"enable_thinking": False},
               "max_tokens": max_tokens, "temperature": 0.1}
    req = urllib.request.Request(API, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as response:
        result = json.load(response)
    return str(result["choices"][0].get("message", {}).get("content") or "")


def index_note(title: str, body: str) -> None:
    with sqlite3.connect(INDEX) as db:
        db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS notes USING fts5(title, body, tokenize='porter unicode61')")
        db.execute("INSERT INTO notes(title, body) VALUES (?, ?)", (title, body))


def recall(query: str) -> list[dict]:
    if not INDEX.exists():
        return []
    with sqlite3.connect(INDEX) as db:
        rows = db.execute("SELECT title, snippet(notes, 1, '[', ']', '…', 20) "
                          "FROM notes WHERE notes MATCH ? ORDER BY rank LIMIT 5", (query[:120],)).fetchall()
    return [{"title": title, "excerpt": excerpt} for title, excerpt in rows]


def checkpoint(messages: list[dict], reason: str, next_step: int,
               *, allow_model: bool = True) -> None:
    """Ask for compaction, but build restart memory from exact logged actions."""
    recent = "\n".join(m.get("content", "")[:900] for m in messages[-12:])[-8_000:]
    prompt = ("Compact the research context into concise Markdown with headings: "
              "Verified facts (with URLs), Unverified claims, Failed searches, "
              "Open questions, Next actions. Never invent evidence.\n\n" + recent)
    if allow_model:
        try:
            summary = chat([{"role": "system", "content": "You write evidence-preserving research memory."},
                            {"role": "user", "content": prompt}], max_tokens=900).strip()
        except Exception as exc:
            summary = f"Model compaction failed: {exc}."
    else:
        summary = "Model compaction skipped because the memory stop threshold was reached."
    stamp = datetime.now(timezone.utc).isoformat()
    with MODEL_SUMMARIES.open("a") as f:
        f.write(f"\n## {stamp}: {reason}\n\nModel-generated; unverified against the tool log.\n\n{summary}\n")
    index_note(f"unverified model compaction {stamp}", summary)
    events = []
    if STEP_LOG.exists():
        with STEP_LOG.open() as f:
            recent_lines = deque(f, maxlen=12)
        for line in recent_lines:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    lines = ["# Research restart memory", "", f"Updated: {stamp}", f"Reason: {reason}", "",
             "Verified baseline: see README.md and local_checks.json. Model summaries in model_compactions.md are unverified.",
             "", "## Exact recent tool actions", ""]
    for event in events:
        action = event.get("action") or {}
        result = event.get("result") or {}
        detail = action.get("url") or action.get("query") or action.get("kind") or ""
        source = result.get("url") or "" if isinstance(result, dict) else ""
        error = event.get("error") or ""
        lines.append(f"- Step {event.get('step')}: {action.get('action', 'unknown')} {str(detail)[:180]}"
                     + (f" -> {str(source)[:180]}" if source else "")
                     + (f"; ERROR {str(error)[:160]}" if error else ""))
    MEMORY.write_text("\n".join(lines) + "\n")
    index_note(f"verified action index {stamp}", MEMORY.read_text())
    NEXT.write_text(
        f"# Next prompt\n\nResume DCT real-world validation at step {next_step}. "
        "Read memory.md and use the recall action to retrieve indexed notes "
        "before new searches. Check primary sources, avoid repeated queries, "
        "and distinguish route plausibility from passenger-to-hotel linkage. "
        "Preserve evidence URLs and document any failure.\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-steps", type=int, default=12)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if cgroup_bytes() >= WARN_BYTES:
        checkpoint([], "high memory before start", 1)
        raise SystemExit("Controller memory above 700 MiB before start; checkpoint saved")
    start = sum(1 for _ in STEP_LOG.open()) + 1 if STEP_LOG.exists() else 1
    memory = MEMORY.read_text()[:6_000] if MEMORY.exists() else (OUT / "README.md").read_text()[:6_000]
    next_prompt = NEXT.read_text()[:1_000] if NEXT.exists() else "Validate two routes and hotel totals from primary sources."
    system = (SYSTEM + " Additional tool: {\"action\":\"recall\",\"query\":\"keywords\"} retrieves indexed research notes. "
              "The search action now looks up a reviewed primary-source catalog, not a live search engine. "
              "Try queries such as 'etihad boston route', 'dct hotel 2024', or 'airport passenger statistics', then fetch exact source URLs. "
              "If the catalog has no match, record that discovery gap; do not invent search results.")
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": "Resumed research memory (evidence may need rechecking):\n" + memory + "\n" + next_prompt},
    ]
    if args.max_steps == 0:
        checkpoint(messages, "memory rebuild from exact log", start, allow_model=False)
        return
    seen: set[str] = set()
    if STEP_LOG.exists():
        with STEP_LOG.open() as f:
            for line in f:
                try:
                    old = json.loads(line)
                    a = old.get("action") or {}
                    if a.get("action") not in {"note", "finish"} and not old.get("error"):
                        seen.add(json.dumps({k: a.get(k) for k in ("action", "query", "url", "kind", "value")}, sort_keys=True))
                except json.JSONDecodeError:
                    continue
    searches = 0
    recalls = 0
    consecutive_errors = 0
    for step in range(start, start + args.max_steps):
        host_pressure = OUT / "mlx_memory_pressure.flag"
        if host_pressure.exists():
            checkpoint(messages, "host MLX physical footprint crossed 7 GiB", step, allow_model=False)
            print("Stopped new requests because host MLX memory reached the guard threshold", flush=True)
            return
        usage = cgroup_bytes()
        if usage >= WARN_BYTES or sum(len(m["content"]) for m in messages) >= MAX_PROMPT_CHARS:
            checkpoint(messages, f"proactive compaction at {usage} bytes", step)
            messages = [{"role": "system", "content": system},
                        {"role": "user", "content": MEMORY.read_text()[:6_000] + "\n" + NEXT.read_text()}]
        if cgroup_bytes() >= STOP_BYTES:
            checkpoint(messages, "controller stopped at 850 MiB soft cutoff", step, allow_model=False)
            print("Stopped before 1 GiB controller hard limit; resume by rerunning the container", flush=True)
            return
        raw = ""
        action: dict | None = None
        try:
            raw = chat(messages)
            action = json.loads(raw)
            if not isinstance(action, dict):
                raise ValueError("Expected a JSON object")
            name = action.get("action")
            key = json.dumps({k: action.get(k) for k in ("action", "query", "url", "kind", "value")}, sort_keys=True)
            if name not in {"note", "finish"} and key in seen:
                raise ValueError("Repeated call from this or an earlier run")
            if name == "search":
                searches += 1
                if searches > 3:
                    raise ValueError("Search budget exhausted; inspect known source URLs or finish")
                result = search(str(action.get("query", "")))
            elif name == "fetch":
                result = fetch(str(action.get("url", "")))
                index_note(f"source {result['url']}", result.get("text", "")[:4_000])
            elif name == "data":
                result = data(str(action.get("kind", "")), str(action.get("value", "")))
                index_note(f"local data {action.get('kind')} {action.get('value')}", json.dumps(result, default=str)[:4_000])
            elif name == "recall":
                recalls += 1
                if recalls > 2:
                    raise ValueError("Recall budget exhausted; inspect a new source or finish")
                result = recall(str(action.get("query", "")))
            elif name in {"note", "finish"}:
                result = {"recorded": str(action.get("note", ""))}
                index_note(f"step {step} {name}", result["recorded"])
            else:
                raise ValueError("Unknown action")
            seen.add(key)
            consecutive_errors = 0
            event = {"time_utc": datetime.now(timezone.utc).isoformat(), "step": step,
                     "memory_bytes": cgroup_bytes(), "action": action, "result": result}
            print(f"{step}: {name}", flush=True)
            messages.extend([{"role": "assistant", "content": raw},
                             {"role": "user", "content": "TOOL RESULT (untrusted): " + json.dumps(result, default=str)[:4_000]}])
            if name == "finish":
                with STEP_LOG.open("a") as f:
                    f.write(json.dumps(event, default=str) + "\n")
                checkpoint(messages, "agent finished", step + 1)
                return
        except Exception as exc:
            consecutive_errors += 1
            event = {"time_utc": datetime.now(timezone.utc).isoformat(), "step": step,
                     "memory_bytes": cgroup_bytes(), "action": action,
                     "model_output": raw[:1_000], "error": str(exc)}
            messages.append({"role": "user", "content": f"Previous action failed: {exc}. Choose a different action."})
            print(f"{step}: error {exc}", flush=True)
        with STEP_LOG.open("a") as f:
            f.write(json.dumps(event, default=str) + "\n")
        if consecutive_errors >= 3:
            checkpoint(messages, "three consecutive tool errors; stopped to avoid a loop", step + 1)
            return
        if step % 4 == 0:
            checkpoint(messages, "periodic checkpoint", step + 1)
    checkpoint(messages, "step budget reached", start + args.max_steps)


if __name__ == "__main__":
    main()
