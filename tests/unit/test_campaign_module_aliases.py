"""Legacy import names share each authoritative module."""

import importlib
import sys

import pytest


@pytest.mark.parametrize(
    ("module", "package"),
    [
        ("campaign_state", "tizen_campaign_core"),
        ("_campaign_workspace", "tizen_campaign_core"),
        ("previous_evidence", "tizen_campaign_core"),
        ("suppress_policy", "tizen_campaign_core"),
        ("aggregate", "tizen_campaign_core"),
        ("derive_commit", "tizen_campaign_core"),
        ("submission_identity", "tizen_campaign_core"),
        ("_sandbox_git", "tizen_campaign_core"),
        ("campaign_repair_step", "tizen_campaign_repair"),
        ("sandbox_submit", "tizen_sandbox_submit"),
        ("qb_trigger", "tizen_qb_verify"),
        ("qb_result_fetch", "tizen_qb_verify"),
        ("qb_discovery", "tizen_qb_verify"),
        ("qb_binding", "tizen_qb_verify"),
        ("qb_evidence", "tizen_qb_verify"),
        ("qb_result_html", "tizen_qb_verify"),
        ("qb_browser", "tizen_qb_verify"),
        ("qb_config", "tizen_qb_verify"),
        ("qb_redact", "tizen_qb_verify"),
    ],
)
def test_legacy_module_is_authoritative_module(module: str, package: str) -> None:
    old_name = f"ci_triage.{module}"
    new_name = f"{package}.{module}"
    importlib.import_module(old_name)
    importlib.import_module(new_name)
    assert sys.modules[old_name] is sys.modules[new_name]
