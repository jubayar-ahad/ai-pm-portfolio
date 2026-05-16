"""Refusal canonicalization for the tool-use-agent.

Mirrors ``rag-app/rag_app/verify.py``: ``REFUSAL_SENTENCE`` is defined
exactly once in this build and imported by the agent loop, so the
threshold-bypass output and the model-following-the-prompt output are
byte-identical and the future evals harness can bucket all refusal
paths via a single equality check across both builds.

This module owns three pieces of slice-4 contract:

1. ``REFUSAL_SENTENCE`` — single source of truth for the canonical
   refusal string, byte-identical with ``rag-app/rag_app/verify.py``.
2. ``canonical_call_key`` / ``detect_repeated_error`` — the
   deterministic detector for the "two consecutive tool errors on
   the same input" termination condition. The agent loop calls
   ``detect_repeated_error`` between steps and refuses if it returns
   a non-empty key.
3. ``is_model_refusal`` — strict equality check (after
   ``str.strip()``) so the agent can tag the ``end_turn`` path with
   ``refusal_reason="model_refused"`` when the model itself emits
   the canonical sentence per system-prompt rule 1.

All three deterministic refusal paths populate
``AgentResult.refusal_reason`` so the eval harness can group them
without parsing ``final_text``.
"""

from __future__ import annotations

import json
from typing import Iterable, Mapping

REFUSAL_SENTENCE = (
    "I don't have enough information in the provided context to answer this."
)


def canonical_call_key(tool: str, tool_input: Mapping[str, object]) -> str:
    """Stable, hashable key for a ``(tool, input)`` pair.

    Used by the repeated-error detector to compare calls across
    consecutive steps. Keys are JSON-serialized with sorted keys so
    parallel call ordering within a turn does not affect equality.
    """
    return json.dumps(
        {"tool": tool, "input": dict(tool_input)},
        sort_keys=True,
        ensure_ascii=False,
    )


def detect_repeated_error(
    prev_step_error_keys: Iterable[str],
    this_step_error_keys: Iterable[str],
) -> str | None:
    """Return the first call key that errored in both steps, else None.

    Equality is canonical (``canonical_call_key``). A return value of
    ``None`` means no consecutive same-input failure was observed for
    this pair of steps.
    """
    prev_set = set(prev_step_error_keys)
    for key in this_step_error_keys:
        if key in prev_set:
            return key
    return None


def is_model_refusal(text: str) -> bool:
    """True iff the model's end_turn text is the canonical refusal sentence.

    Strict ``str.strip()`` equality — extra prose around the sentence
    counts as a partial answer, not a refusal, per system-prompt rule
    1 which requires the model to reply *exactly* with the sentence
    and nothing else.
    """
    return text.strip() == REFUSAL_SENTENCE
