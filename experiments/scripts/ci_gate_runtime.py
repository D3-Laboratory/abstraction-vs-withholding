#!/usr/bin/env python3
"""Shared two-action runtime for Generic Gate and CI Gate."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


ALLOWED_ACTIONS = {"PASS_THROUGH", "TRANSFORM_AND_RELEASE"}


class GateDecisionError(ValueError):
    """The gate output cannot be applied without changing the experiment contract."""


@dataclass(frozen=True)
class AppliedGateDecision:
    action: str
    released_message: str
    edits: tuple[dict[str, Any], ...]
    fallback: bool = False
    fallback_reason: str | None = None


def extract_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object, accepting one surrounding Markdown code fence."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            stripped = "\n".join(lines[1:-1])
            if stripped.lstrip().startswith("json"):
                stripped = stripped.lstrip()[4:].lstrip()
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise GateDecisionError(f"gate output is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise GateDecisionError("gate output must be a JSON object")
    return value


def _resolve_occurrence(text: str, span: str, occurrence: int) -> tuple[int, int]:
    if not span:
        raise GateDecisionError("verbatim_span must not be empty")
    if isinstance(occurrence, bool) or not isinstance(occurrence, int) or occurrence < 1:
        raise GateDecisionError("occurrence must be a positive integer")

    offset = 0
    start = -1
    for _ in range(occurrence):
        start = text.find(span, offset)
        if start < 0:
            raise GateDecisionError(
                f"verbatim_span occurrence {occurrence} does not exist in candidate"
            )
        offset = start + len(span)
    return start, start + len(span)


def apply_gate_decision(candidate: str, decision: dict[str, Any]) -> AppliedGateDecision:
    """Validate and apply exact-span edits while preserving every untouched byte."""
    if not isinstance(candidate, str):
        raise GateDecisionError("candidate must be a string")
    action = decision.get("action")
    if action not in ALLOWED_ACTIONS:
        raise GateDecisionError(f"unsupported action: {action!r}")
    edits = decision.get("edits")
    if not isinstance(edits, list):
        raise GateDecisionError("edits must be an array")

    if action == "PASS_THROUGH":
        if edits:
            raise GateDecisionError("PASS_THROUGH requires an empty edits array")
        return AppliedGateDecision(action, candidate, ())

    if not edits:
        raise GateDecisionError("TRANSFORM_AND_RELEASE requires at least one edit")

    resolved: list[tuple[int, int, dict[str, Any]]] = []
    for index, edit in enumerate(edits):
        if not isinstance(edit, dict):
            raise GateDecisionError(f"edit {index} must be an object")
        allowed_keys = {"verbatim_span", "occurrence", "replacement", "reason_codes"}
        unknown = set(edit) - allowed_keys
        if unknown:
            raise GateDecisionError(f"edit {index} has unknown keys: {sorted(unknown)}")
        span = edit.get("verbatim_span")
        replacement = edit.get("replacement")
        occurrence = edit.get("occurrence", 1)
        reason_codes = edit.get("reason_codes")
        if not isinstance(span, str) or not isinstance(replacement, str):
            raise GateDecisionError(f"edit {index} span and replacement must be strings")
        if not isinstance(reason_codes, list) or not reason_codes or not all(
            isinstance(code, str) and code for code in reason_codes
        ):
            raise GateDecisionError(f"edit {index} requires non-empty reason_codes")
        if replacement == span:
            continue
        start, end = _resolve_occurrence(candidate, span, occurrence)
        normalized = {
            "verbatim_span": span,
            "occurrence": occurrence,
            "replacement": replacement,
            "reason_codes": reason_codes,
            "start": start,
            "end": end,
        }
        resolved.append((start, end, normalized))

    if not resolved:
        raise GateDecisionError("TRANSFORM_AND_RELEASE contains only no-op edits")

    resolved.sort(key=lambda item: (item[0], item[1]))
    for previous, current in zip(resolved, resolved[1:]):
        if current[0] < previous[1]:
            raise GateDecisionError("gate edits overlap")

    released = candidate
    for start, end, edit in reversed(resolved):
        released = released[:start] + edit["replacement"] + released[end:]
    if released == candidate:
        raise GateDecisionError("TRANSFORM_AND_RELEASE must change the candidate")

    return AppliedGateDecision(
        action=action,
        released_message=released,
        edits=tuple(item[2] for item in resolved),
    )


def conservative_fallback(candidate: str, reason: str) -> AppliedGateDecision:
    """Return the fixed two-action fallback; never invent a hidden DENY state."""
    replacement = (
        "I can continue with the task, but I cannot include private details that are "
        "not necessary for this recipient. Please proceed using only the non-sensitive "
        "requirements already provided."
    )
    decision = {
        "action": "TRANSFORM_AND_RELEASE",
        "edits": [
            {
                "verbatim_span": candidate,
                "occurrence": 1,
                "replacement": replacement,
                "reason_codes": ["PARSER_OR_CONTRACT_FALLBACK"],
            }
        ],
    }
    applied = apply_gate_decision(candidate, decision)
    return AppliedGateDecision(
        action=applied.action,
        released_message=applied.released_message,
        edits=applied.edits,
        fallback=True,
        fallback_reason=reason,
    )
