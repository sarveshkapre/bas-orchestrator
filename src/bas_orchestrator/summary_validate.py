from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any


def validate_summary(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return ["summary must be a JSON object"]

    errors: list[str] = []
    required = {
        "ok",
        "campaign_name",
        "run_id",
        "started_at",
        "finished_at",
        "score",
        "summary",
        "results",
    }

    missing = sorted(required - set(payload.keys()))
    for field in missing:
        errors.append(f"missing field: {field}")

    if "ok" in payload and not isinstance(payload["ok"], bool):
        errors.append("field ok must be boolean")
    if "campaign_name" in payload and not isinstance(payload["campaign_name"], str):
        errors.append("field campaign_name must be string")
    if "run_id" in payload and not isinstance(payload["run_id"], str):
        errors.append("field run_id must be string")
    if "started_at" in payload and not isinstance(payload["started_at"], str):
        errors.append("field started_at must be string")
    if "finished_at" in payload and not isinstance(payload["finished_at"], str):
        errors.append("field finished_at must be string")
    if "score" in payload and not isinstance(payload["score"], (int, float)):
        errors.append("field score must be number")

    if "summary" in payload:
        summary = payload["summary"]
        if not isinstance(summary, dict):
            errors.append("field summary must be object")
        else:
            for key in ("total", "passed", "failed", "errored", "skipped"):
                if key not in summary:
                    errors.append(f"summary missing field: {key}")
                    continue
                value = summary[key]
                if not isinstance(value, int) or value < 0:
                    errors.append(f"summary field {key} must be non-negative integer")

    if "results" in payload:
        results = payload["results"]
        if not isinstance(results, list):
            errors.append("field results must be array")
        else:
            for index, item in enumerate(results):
                if not isinstance(item, dict):
                    errors.append(f"results[{index}] must be object")
                    continue
                _validate_result(item, index, errors)

    return errors


def _validate_result(item: dict[str, Any], index: int, errors: list[str]) -> None:
    required = {"module_id", "status", "duration_ms", "evidence_ref"}
    missing = sorted(required - set(item.keys()))
    for field in missing:
        errors.append(f"results[{index}] missing field: {field}")

    if "module_id" in item and not isinstance(item["module_id"], str):
        errors.append(f"results[{index}].module_id must be string")
    if "status" in item:
        if not isinstance(item["status"], str):
            errors.append(f"results[{index}].status must be string")
        elif item["status"] not in {"pass", "fail", "skipped", "error"}:
            errors.append(f"results[{index}].status must be pass/fail/skipped/error")
    if "duration_ms" in item:
        value = item["duration_ms"]
        if not isinstance(value, int) or value < 0:
            errors.append(f"results[{index}].duration_ms must be non-negative integer")
    if "evidence_ref" in item and not isinstance(item["evidence_ref"], str):
        errors.append(f"results[{index}].evidence_ref must be string")
    if "notes" in item and item["notes"] is not None and not isinstance(item["notes"], str):
        errors.append(f"results[{index}].notes must be string or null")


def diff_summary(
    golden: object,
    candidate: object,
    *,
    ignore_fields: Iterable[str] = (),
    ignore_paths: Iterable[str] = (),
) -> list[str]:
    if not isinstance(golden, dict):
        return ["golden summary must be a JSON object"]
    if not isinstance(candidate, dict):
        return ["candidate summary must be a JSON object"]

    ignore = set(ignore_fields)
    golden_norm = {key: value for key, value in golden.items() if key not in ignore}
    candidate_norm = {key: value for key, value in candidate.items() if key not in ignore}

    diffs: list[str] = []
    patterns = [_normalize_path_pattern(pattern) for pattern in ignore_paths]
    _diff_values(golden_norm, candidate_norm, path="$", diffs=diffs, ignore_patterns=patterns)
    return diffs


def _diff_values(
    golden: object,
    candidate: object,
    *,
    path: str,
    diffs: list[str],
    ignore_patterns: list[str],
) -> None:
    if _should_ignore_path(path, ignore_patterns):
        return

    if isinstance(golden, dict) and isinstance(candidate, dict):
        golden_keys = set(golden.keys())
        candidate_keys = set(candidate.keys())
        for key in sorted(golden_keys - candidate_keys):
            diffs.append(f"{path}.{key} missing in candidate")
        for key in sorted(candidate_keys - golden_keys):
            diffs.append(f"{path}.{key} extra in candidate")
        for key in sorted(golden_keys & candidate_keys):
            _diff_values(
                golden[key],
                candidate[key],
                path=f"{path}.{key}",
                diffs=diffs,
                ignore_patterns=ignore_patterns,
            )
        return

    if isinstance(golden, list) and isinstance(candidate, list):
        if len(golden) != len(candidate):
            diffs.append(
                f"{path} length differs (golden {len(golden)} vs candidate {len(candidate)})"
            )
        for index, (gold_item, cand_item) in enumerate(zip(golden, candidate, strict=False)):
            _diff_values(
                gold_item,
                cand_item,
                path=f"{path}[{index}]",
                diffs=diffs,
                ignore_patterns=ignore_patterns,
            )
        return

    if golden != candidate:
        diffs.append(f"{path} differs (golden {golden!r} vs candidate {candidate!r})")


def _normalize_path_pattern(pattern: str) -> str:
    if pattern.startswith("$"):
        return pattern
    if pattern.startswith("."):
        return f"${pattern}"
    return f"$.{pattern}"


def _should_ignore_path(path: str, patterns: list[str]) -> bool:
    if not patterns:
        return False
    for pattern in patterns:
        regex = _pattern_to_regex(pattern)
        if re.fullmatch(regex, path):
            return True
    return False


def _pattern_to_regex(pattern: str) -> str:
    placeholder = "__IDX__"
    pattern = pattern.replace("[*]", placeholder)
    escaped = ""
    for char in pattern:
        if char == "*":
            escaped += ".*"
        elif char == "?":
            escaped += "."
        else:
            escaped += re.escape(char)
    escaped = escaped.replace(re.escape(placeholder), r"\[\d+\]")
    return escaped
