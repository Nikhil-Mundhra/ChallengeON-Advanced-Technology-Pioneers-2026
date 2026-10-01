#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import urllib.request


PROMPT = (
    "Do not use tools. Write exactly 60 numbered, single-sentence observations about "
    "reliable data pipelines. Use concrete technical language and no headings or preamble."
)
OPEN_CODE_MODELS = (
    "opencode/longcat-2.5-preview-free",
    "opencode/big-pickle",
    "opencode/space-bunny-free",
    "opencode/nemotron-3-ultra-free",
)


def qwen_run() -> dict[str, object]:
    payload = {
        "model": "mlx-community/Qwen3.5-4B-MLX-4bit",
        "messages": [{"role": "user", "content": PROMPT}],
        "stream": False,
        "temperature": 0,
        "max_tokens": 1024,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    request = urllib.request.Request(
        "http://localhost:8000/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=300) as response:
        result = json.load(response)
    elapsed = time.perf_counter() - started
    usage = result.get("usage", {})
    output = int(usage.get("completion_tokens", 0))
    return {
        "model": payload["model"],
        "backend": "local_qwen",
        "seconds": round(elapsed, 3),
        "visible_tokens": output,
        "reasoning_tokens": 0,
        "generated_tokens": output,
        "visible_tokens_per_second": round(output / elapsed, 2),
        "generated_tokens_per_second": round(output / elapsed, 2),
        "finish_reason": result["choices"][0].get("finish_reason"),
    }


def opencode_run(model: str) -> dict[str, object]:
    command = [
        "opencode", "run", "--model", model, "--format", "json", "--pure", PROMPT
    ]
    if model == "opencode/space-bunny-free":
        command[-1:-1] = ["--variant", "medium"]
    environment = {
        **os.environ,
        "OPENCODE_DISABLE_CLAUDE_CODE": "1",
        "OPENCODE_DISABLE_DEFAULT_PLUGINS": "1",
        "OPENCODE_DISABLE_PROJECT_CONFIG": "1",
    }
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="agent-speed-") as directory:
        result = subprocess.run(
            command,
            cwd=directory,
            env=environment,
            text=True,
            capture_output=True,
            timeout=300,
            check=False,
        )
    elapsed = time.perf_counter() - started
    visible = reasoning = 0
    finish_reason = None
    text_chars = 0
    for line in result.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        part = event.get("part", {})
        if event.get("type") == "text":
            text_chars += len(str(part.get("text", "")))
        elif event.get("type") == "step_finish":
            tokens = part.get("tokens", {})
            visible += int(tokens.get("output", 0) or 0)
            reasoning += int(tokens.get("reasoning", 0) or 0)
            finish_reason = part.get("reason")
    generated = visible + reasoning
    return {
        "model": model,
        "backend": "opencode",
        "seconds": round(elapsed, 3),
        "visible_tokens": visible,
        "reasoning_tokens": reasoning,
        "generated_tokens": generated,
        "visible_tokens_per_second": round(visible / elapsed, 2),
        "generated_tokens_per_second": round(generated / elapsed, 2),
        "text_chars": text_chars,
        "finish_reason": finish_reason,
        "exit_code": result.returncode,
        "stderr": result.stderr[-500:] if result.returncode else "",
    }


def main() -> None:
    active_audit = subprocess.run(
        ["pgrep", "-f", "run_data_issues_audit.py run"],
        text=True,
        capture_output=True,
        check=False,
    )
    if active_audit.returncode == 0:
        raise SystemExit(
            "Refusing a contended benchmark: pause the active data-audit run first."
        )
    # Warm local weights and kernels before the measured request.
    qwen_run()
    rows = [qwen_run(), *(opencode_run(model) for model in OPEN_CODE_MODELS)]
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
