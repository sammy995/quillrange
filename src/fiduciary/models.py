"""Single entry point for all model calls. mock:* models never touch the network."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

DEFAULT_MOCK_DIR = "tests/fixtures/mock_responses"
CRITERION_RE = re.compile(r"\[([A-Z0-9]+-[A-Z]+-\d+-r\d+)\]")

# Last sampling kwargs seen by complete() — mutable so importers see updates.
LAST_CALL: dict[str, Any] = {}


def _mock(model: str, messages: list[dict], tag: str | None) -> str:
    last = messages[-1]["content"]
    if model == "mock:echo":
        return last
    if model == "mock:judge":
        ids = CRITERION_RE.findall(last)
        scores = [{"criterion_id": i, "score": 8, "rationale": "mock"} for i in ids]
        return json.dumps({"scores": scores})
    if model == "mock:commajudge":  # valid scores but trailing comma (repairable)
        ids = CRITERION_RE.findall(last)
        body = ", ".join(
            f'{{"criterion_id": "{i}", "score": 6, "rationale": "mock"}}' for i in ids)
        return '{"scores": [' + body + ',]}'
    if model == "mock:brokenjudge":  # unparseable garbage (must be skipped, not crash)
        return "sorry, I cannot output JSON right now."
    if model.startswith("mock:fixture:"):
        variant = model.split(":", 2)[2]
        if tag is None:
            raise ValueError("mock:fixture requires tag=scenario_id")
        root = Path(os.environ.get("FIDUCIARY_MOCK_DIR", DEFAULT_MOCK_DIR))
        return (root / variant / f"{tag}.txt").read_text(encoding="utf-8")
    raise ValueError(f"unknown mock model: {model}")


def complete(
    model: str,
    messages: list[dict],
    temperature: float = 0.0,
    tag: str | None = None,
    *,
    top_p: float | None = None,
    max_tokens: int | None = None,
    seed: int | None = None,
) -> str:
    LAST_CALL.clear()
    LAST_CALL.update({
        "model": model,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "seed": seed,
        "tag": tag,
        "n_messages": len(messages),
    })
    if model.startswith("mock:"):
        return _mock(model, messages, tag)
    from litellm import completion  # imported lazily so tests never need it

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "num_retries": 3,
    }
    if top_p is not None:
        kwargs["top_p"] = top_p
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if seed is not None:
        kwargs["seed"] = seed
    resp = completion(**kwargs)
    return resp.choices[0].message.content
