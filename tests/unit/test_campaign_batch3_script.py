import re
import shlex
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "tizen-clang-campaign/SKILL.md"
COMMANDS = {
    "tizen_campaign_intake": {"campaign-start-check", "campaign-add-unit", "campaign-discover"},
    "tizen_baseline_reproduce": {"baseline-reproduce"},
    "tizen_campaign_repair": {"suppress-policy", "campaign-repair-step", "propose-fix"},
    "tizen_campaign_kb": {"campaign-kb-sync"},
    "tizen_sandbox_submit": {"sandbox-submit"},
    "tizen_qb_verify": {"qb-trigger", "qb-result-fetch", "qb-discover"},
    "tizen_review_submit": {"review-submit"},
    "tizen_campaign_report": {
        "campaign-finish-unit",
        "campaign-release-worktrees",
        "campaign-report",
    },
}


def check_script(text: str) -> None:
    blocks = re.findall(r"```(?:bash|sh)\n(.*?)```", text, re.S)
    assert blocks
    seen = set()
    for block in blocks:
        assert not any(word in block for word in ("build-verify", "gbs build", "iter_"))
        normalized = block.replace("\\\n", " ").strip()
        commands = normalized.split("&&")
        for index, command in enumerate(commands):
            argv = shlex.split(command)
            assert argv[:2] == ["python", "-m"]
            assert argv[2] in COMMANDS and argv[3] in COMMANDS[argv[2]]
            seen.add(argv[3])
            if argv[3] == "campaign-repair-step":
                assert index > 0
                previous = shlex.split(commands[index - 1])
                assert previous[:5] == [
                    "python",
                    "-m",
                    "tizen_campaign_repair",
                    "suppress-policy",
                    "check",
                ]
                assert previous[previous.index("--source-kind") + 1] == "$SOURCE_KIND"
    assert seen == set().union(*COMMANDS.values())


def test_orchestration_commands_and_shared_state_root() -> None:
    text = SKILL.read_text()
    check_script(text)
    template = (SKILL.parent / "references/campaign-kickoff-template.md").read_text()
    assert "STATE_ROOT" in template
    assert "generated" in text and "suppress" in text and "forbidden" in text
    assert "REPAIR_ROUND_RUNNING" in text


@pytest.mark.parametrize(
    "bad",
    [
        "python -m tizen_build_verify build-verify",
        "gbs build --arch aarch64",
        "python -m tizen_campaign_repair campaign-repair-step --path ws/iter_1",
    ],
)
def test_script_forbidden_command_red_examples(bad: str) -> None:
    with pytest.raises(AssertionError):
        check_script(SKILL.read_text() + "\n```bash\n" + bad + "\n```\n")


def test_policy_forbidden_cannot_fall_through_to_repair() -> None:
    text = SKILL.read_text()
    with pytest.raises(AssertionError):
        check_script(text.replace('"$SOURCE_KIND" && \\\n', '"$SOURCE_KIND"\n'))
