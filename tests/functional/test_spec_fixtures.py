import time
from pathlib import Path

from gbs_analyzer.tizen.spec_minimal import SpecMinimalParser

FIXTURES = Path(__file__).parents[1] / "fixtures"


CASES = {
    "spec_basic": {
        "package": "demo",
        "spec": "demo.spec",
        "phase": "%build",
        "buildrequires": ["gcc", "make"],
        "patch_count": 1,
        "source_count": 1,
        "last_command": "make",
        "warning": None,
    },
    "spec_macro": {
        "package": "demo-macro",
        "spec": "demo-macro.spec",
        "phase": "%build",
        "buildrequires": ["pkgconfig(foo) >= 1.0"],
        "patch_count": 0,
        "source_count": 1,
        "last_command": "make -j4",
        "warning": "macros_present_not_expanded",
    },
    "spec_conditionals": {
        "package": "conditional",
        "spec": "conditional.spec",
        "phase": "%build",
        "buildrequires": ["pkgconfig(tizen)", "gcc"],
        "patch_count": 0,
        "source_count": 1,
        "last_command": "make conditional",
        "warning": "conditionals_present_not_evaluated",
    },
    "spec_subpackage": {
        "package": "subdemo",
        "spec": "subdemo.spec",
        "phase": "%build",
        "buildrequires": ["gcc"],
        "patch_count": 0,
        "source_count": 1,
        "last_command": "make all",
        "warning": "subpackages_present_not_resolved",
    },
    "spec_install_failure": {
        "package": "installfail",
        "spec": "installfail.spec",
        "phase": "%install",
        "buildrequires": ["make"],
        "patch_count": 1,
        "source_count": 1,
        "last_command": "install -m 0755 missing /tmp/buildroot/usr/bin/missing",
        "warning": "macros_present_not_expanded",
    },
}


def test_spec_fixtures_extract_minimal_data() -> None:
    for name, expected in CASES.items():
        fixture = FIXTURES / name
        spec_path = SpecMinimalParser.find_spec_file(str(expected["package"]), fixture)
        assert spec_path.name == expected["spec"]

        parser = SpecMinimalParser(spec_path, buildlog_path=fixture / "buildlog")
        assert parser.extract_buildrequires() == expected["buildrequires"]
        assert len(parser.extract_patches()) == expected["patch_count"]
        assert len(parser.extract_sources()) == expected["source_count"]
        assert parser.extract_section(str(expected["phase"]))

        context = parser.extract_section_failure_context(str(expected["phase"]))
        assert context["last_command"] == expected["last_command"]
        assert context["spec_section_text"]

        status = parser.get_parse_status()
        assert status["confidence"] == "partial"
        if expected["warning"]:
            assert expected["warning"] in status["warnings"]


def test_spec_fixture_batch_under_200ms() -> None:
    started = time.perf_counter()
    for name, expected in CASES.items():
        fixture = FIXTURES / name
        parser = SpecMinimalParser(
            fixture / str(expected["spec"]),
            buildlog_path=fixture / "buildlog",
        )
        parser.extract_buildrequires()
        parser.extract_patches()
        parser.extract_sources()
        parser.extract_section(str(expected["phase"]))
        parser.extract_section_failure_context(str(expected["phase"]))
        parser.get_parse_status()

    elapsed_ms = (time.perf_counter() - started) * 1000
    assert elapsed_ms < 200.0
