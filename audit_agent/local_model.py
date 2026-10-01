from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class OpenAICompatibleClient:
    """Minimal client for the local MLX OpenAI-compatible chat endpoint."""

    endpoint: str = "http://localhost:8000/v1/chat/completions"
    model: str = "mlx-community/Qwen3.5-4B-MLX-4bit"
    timeout_seconds: int = 300
    max_tokens: int = 1024
    max_prompt_chars: int = 280_000

    def _bounded_messages(
        self, messages: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        """Keep local prefills bounded while retaining instructions and recent evidence."""
        if sum(len(message.get("content", "")) for message in messages) <= self.max_prompt_chars:
            return messages

        head = messages[:2]
        head_chars = sum(len(message.get("content", "")) for message in head)
        notice = {
            "role": "user",
            "content": (
                "CONTEXT COMPACTION: older turns were omitted. Use retained evidence; "
                "request a narrow tool call again if needed."
            ),
        }
        remaining = max(self.max_prompt_chars - head_chars - len(notice["content"]), 0)
        tail: list[dict[str, str]] = []
        for message in reversed(messages[2:]):
            size = len(message.get("content", ""))
            if size > remaining:
                break
            tail.append(message)
            remaining -= size
        return [*head, notice, *reversed(tail)]

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        json_mode: bool = True,
        temperature: float = 0.1,
        max_tokens: int | None = None,
        timeout_seconds: int | None = None,
    ) -> str:
        # mlx_lm 0.31.3 exposes thinking separately from assistant content. Keep
        # it off for the bounded JSON protocol so the output budget reaches the
        # actual response instead of being consumed by a reasoning preamble.
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self._bounded_messages(messages),
            "stream": True,
            "temperature": temperature,
            "max_tokens": max_tokens or self.max_tokens,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        try:
            timeout = timeout_seconds or self.timeout_seconds
            response = subprocess.run(
                [
                    "curl",
                    "-sS",
                    "--fail-with-body",
                    "--max-time",
                    str(timeout),
                    "--speed-limit",
                    "1",
                    "--speed-time",
                    str(min(300, timeout)),
                    "--no-buffer",
                    self.endpoint,
                    "-H",
                    "Content-Type: application/json",
                    "--data-binary",
                    "@-",
                ],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                timeout=timeout + 5,
                check=False,
            )
            if response.returncode != 0:
                raise RuntimeError(response.stderr.strip() or response.stdout.strip())
            content = self._response_content(response.stdout)
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError(f"local Qwen endpoint failed: {exc}") from exc
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError(
                "local Qwen returned no assistant content; verify enable_thinking=false"
            )
        return content

    @staticmethod
    def _response_content(raw: str) -> str:
        if raw.lstrip().startswith("{"):
            result = json.loads(raw)
            return str(result["choices"][0].get("message", {}).get("content") or "")
        chunks: list[str] = []
        for line in raw.splitlines():
            if not line.startswith("data: ") or line == "data: [DONE]":
                continue
            event = json.loads(line[6:])
            choices = event.get("choices") or []
            if choices:
                value = choices[0].get("delta", {}).get("content")
                if isinstance(value, str):
                    chunks.append(value)
        return "".join(chunks)


def parse_json_response(content: str) -> dict[str, Any]:
    try:
        value = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"model response was not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("model response must be a JSON object")
    return value
