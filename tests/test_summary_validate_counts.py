from bas_orchestrator.summary_validate import validate_summary_counts


def test_validate_counts_accepts_full_summary() -> None:
    summary = {"total": 5, "passed": 3, "failed": 1, "errored": 0, "skipped": 1}
    assert validate_summary_counts(summary) == []


def test_validate_counts_detects_missing_fields() -> None:
    summary = {"total": 5, "passed": 3}
    errors = validate_summary_counts(summary)
    assert any("missing field" in error for error in errors)


def test_validate_counts_rejects_negative_values() -> None:
    summary = {"total": 1, "passed": -1, "failed": 0, "errored": 0, "skipped": 0}
    errors = validate_summary_counts(summary)
    assert any("non-negative integer" in error for error in errors)
