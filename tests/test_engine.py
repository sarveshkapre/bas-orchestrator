from __future__ import annotations

from pathlib import Path

from bas_orchestrator.engine import load_campaign, run_campaign, sign_evidence, verify_evidence


def write_campaign(path: Path) -> None:
    path.write_text(
        """
version: v1
name: "test-campaign"
targets:
  - id: "local-host"
    name: "Local Host"
modules:
  - id: "noop-1"
    module: "noop"
    target_id: "local-host"
    scope_allowlist: ["local"]
    expectations: {}
    params: {}
"""
    )


def test_load_and_run_campaign(tmp_path: Path) -> None:
    campaign_path = tmp_path / "campaign.yaml"
    write_campaign(campaign_path)

    spec = load_campaign(campaign_path)
    evidence = run_campaign(spec)

    assert evidence.campaign_name == "test-campaign"
    assert evidence.summary["total"] == 1
    assert evidence.summary["passed"] == 1


def test_deterministic_run_id(tmp_path: Path) -> None:
    campaign_path = tmp_path / "campaign.yaml"
    write_campaign(campaign_path)

    spec = load_campaign(campaign_path)
    evidence_a = run_campaign(spec, deterministic=True)
    evidence_b = run_campaign(spec, deterministic=True)

    assert evidence_a.run_id == evidence_b.run_id
    assert evidence_a.started_at == evidence_b.started_at
    assert evidence_a.finished_at == evidence_b.finished_at


def test_sign_evidence_is_stable(tmp_path: Path) -> None:
    campaign_path = tmp_path / "campaign.yaml"
    write_campaign(campaign_path)

    spec = load_campaign(campaign_path)
    evidence = run_campaign(spec, deterministic=True)
    signed_a = sign_evidence(evidence, "test-key")
    signed_b = sign_evidence(evidence, "test-key")

    assert signed_a.signature_alg == "hmac-sha256"
    assert signed_a.signature == signed_b.signature


def test_verify_evidence(tmp_path: Path) -> None:
    campaign_path = tmp_path / "campaign.yaml"
    write_campaign(campaign_path)

    spec = load_campaign(campaign_path)
    evidence = run_campaign(spec, deterministic=True)
    signed = sign_evidence(evidence, "test-key")

    assert verify_evidence(signed, "test-key")
    assert not verify_evidence(signed, "other-key")
