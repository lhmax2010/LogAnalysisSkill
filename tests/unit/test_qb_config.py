from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from ci_triage.qb_config import (
    ARCHITECTURES,
    BASE_URL,
    QbConfigError,
    QbProjectNotReady,
    canonical_profile_json,
    parse_qb_config,
    project_for_branch,
)


@pytest.fixture
def config(tmp_path: Path) -> dict:
    executable = tmp_path / "fixture"
    executable.touch()
    return {
        "base_url": BASE_URL,
        "browser": {
            **dict.fromkeys(("node", "playwright_module", "chromium"), str(executable)),
            "login_timeout_seconds": 600,
        },
        "projects": {
            "tizen_base": {
                "enabled": True,
                "overview_id": 100,
                "configuration_path": "root/Tizen-Base-Toolchain/RBS/TRIGGER",
                "project_name": "Tizen-Base-Toolchain",
                "qb_pass_requires_accept": False,
                "form": {
                    "BUILD_TYPE": "Full",
                    "REPO_TYPE": "ALL",
                    "BUILD_REFERENCE": "Ref. Snapshot",
                    "SNAPSHOT_NUM": "@freeze",
                    "PROJECT_BRANCH": "tizen_base",
                    "Immediate Stop With Error": True,
                    "CHILD_CONFIGURATIONS": [ARCHITECTURES],
                    "TARGET_IMAGE": [],
                    "Add Package List": "",
                    "Remove Package List": "",
                },
            },
            "tizen": {"enabled": False},
        },
    }


@pytest.mark.parametrize("snapshot", ["@freeze", "20261010.1"])
@pytest.mark.parametrize("accepted", [False, True])
def test_six_rules_valid_config_and_canonical_profile(config, snapshot, accepted):
    project = config["projects"]["tizen_base"]
    project["form"]["SNAPSHOT_NUM"] = snapshot
    project["qb_pass_requires_accept"] = accepted
    before = copy.deepcopy(config)
    parsed = parse_qb_config(config)
    selected = project_for_branch(parsed, "tizen_base")
    raw = canonical_profile_json(selected, frozen_snapshot="20261010.1")
    profile = json.loads(raw)
    assert set(profile) == {
        "configuration_path",
        "overview_id",
        "project_name",
        "form",
        "qb_pass_requires_accept",
    }
    assert profile["form"]["SNAPSHOT_NUM"] == "20261010.1"
    assert raw == json.dumps(profile, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert config == before
    selected["form"]["BUILD_TYPE"] = "Partial"
    assert parsed == before


@pytest.mark.parametrize("base", ["http://quickbuild.tizen.org", BASE_URL + "/", "https://other"])
def test_rule1_base_url(config, base):
    config["base_url"] = base
    with pytest.raises(QbConfigError) as error:
        parse_qb_config(config)
    assert error.value.code == "INVALID_ARGS"


@pytest.mark.parametrize("key", ["node", "playwright_module", "chromium"])
@pytest.mark.parametrize("path", ["relative/path", "/missing/p5q-fixture", ""])
def test_rule2_paths(config, key, path):
    config["browser"][key] = path
    with pytest.raises(QbConfigError):
        parse_qb_config(config)


@pytest.mark.parametrize("change", ["extra", "missing"])
def test_rule3_exact_form_keys(config, change):
    form = config["projects"]["tizen_base"]["form"]
    if change == "extra":
        form["BUILD NOTES"] = "not configurable"
    else:
        del form["BUILD_TYPE"]
    with pytest.raises(QbConfigError):
        parse_qb_config(config)


@pytest.mark.parametrize("snapshot", [None, "", "  ", 123, [], {}, True])
def test_rule3_snapshot_has_concrete_string_value(config, snapshot):
    config["projects"]["tizen_base"]["form"]["SNAPSHOT_NUM"] = snapshot
    with pytest.raises(QbConfigError):
        parse_qb_config(config)


def test_rule4_branch_must_match(config):
    config["projects"]["tizen_base"]["form"]["PROJECT_BRANCH"] = "tizen"
    with pytest.raises(QbConfigError):
        parse_qb_config(config)


@pytest.mark.parametrize(
    "key,value",
    [
        ("CHILD_CONFIGURATIONS", ["aarch64"]),
        ("CHILD_CONFIGURATIONS", ["standard-armv7l:aarch64"]),
        ("CHILD_CONFIGURATIONS", [ARCHITECTURES, ARCHITECTURES]),
        ("CHILD_CONFIGURATIONS", [ARCHITECTURES, "another-group"]),
        ("CHILD_CONFIGURATIONS", ["standard-armv7l:aarch64:aarch64:x86_64"]),
        ("Immediate Stop With Error", False),
        ("Immediate Stop With Error", 1),
        ("TARGET_IMAGE", ["image"]),
        ("Add Package List", "pkg"),
        ("Remove Package List", "pkg"),
    ],
)
def test_rule5_fixed_architecture_and_failure_fields(config, key, value):
    config["projects"]["tizen_base"]["form"][key] = value
    with pytest.raises(QbConfigError):
        parse_qb_config(config)


@pytest.mark.parametrize("value", [0, 1, "false", None])
def test_rule6_requires_boolean(config, value):
    config["projects"]["tizen_base"]["qb_pass_requires_accept"] = value
    with pytest.raises(QbConfigError):
        parse_qb_config(config)


@pytest.mark.parametrize("branch", ["tizen", "missing"])
def test_project_not_ready(config, branch):
    with pytest.raises(QbProjectNotReady) as error:
        project_for_branch(parse_qb_config(config), branch)
    assert error.value.code == "REJECTED_QB_PROJECT_NOT_READY"


@pytest.mark.parametrize("snapshot", [None, "", "@freeze"])
def test_canonical_freeze_needs_actual_value(config, snapshot):
    with pytest.raises(QbConfigError):
        canonical_profile_json(
            project_for_branch(parse_qb_config(config), "tizen_base"), frozen_snapshot=snapshot
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("configuration_path", "root/other/RBS/TRIGGER"),
        ("overview_id", 101),
        ("project_name", "unicode-测试"),
        ("qb_pass_requires_accept", True),
        ("form", {"SNAPSHOT_NUM": "different"}),
    ],
)
def test_profile_includes_every_freezing_field(config, key, value):
    project = project_for_branch(parse_qb_config(config), "tizen_base")
    before = canonical_profile_json(project, frozen_snapshot="snap")
    project[key] = value
    after = canonical_profile_json(project, frozen_snapshot="snap")
    assert before != after
    assert "\\u" not in after
