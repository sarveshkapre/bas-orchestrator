from __future__ import annotations

from pathlib import Path

import pytest

from bas_orchestrator.engine import CampaignLoadError, load_campaign


def test_unsupported_campaign_version(tmp_path: Path) -> None:
    path = tmp_path / "campaign.yaml"
    path.write_text(
        """
version: v9
name: "bad"
targets: []
modules: []
"""
    )
    with pytest.raises(CampaignLoadError):
        load_campaign(path)
