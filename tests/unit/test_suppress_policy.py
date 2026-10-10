from __future__ import annotations

import copy
import io
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

import pytest
from ci_triage import suppress_policy as policy_module
from ci_triage.cli import main
from ci_triage.suppress_policy import (
    POLICY_RULES_VERSION,
    PolicyHit,
    PolicyInputError,
    evaluate,
)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    return tmp_path


def _spec(edits):
    return {
        "schema_version": "gbs_patch_suggest/edit-spec/v1",
        "patch_name": "policy",
        "edits": edits,
    }


def _whole(repo, file, before, after):
    path = repo / file
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(before, encoding="utf-8", errors="surrogateescape")
    return {"file": file, "old": before, "new": after}


def _evaluate(repo, after, file="CMakeLists.txt", before="# baseline\n", source="generated"):
    return evaluate(_spec([_whole(repo, file, before, after)]), repo, source)


def test_review2_cmake_2000_commands(repo):
    text = "".join(
        f"target_compile_options(target_{index} PRIVATE -Wno-unused-variable)\n"
        for index in range(2000)
    )
    spec = _spec([_whole(repo, "CMakeLists.txt", "# baseline\n", text)])
    start = time.perf_counter()
    result = evaluate(spec, repo, "generated")
    elapsed = time.perf_counter() - start
    print(f"commands=2000 elapsed_seconds={elapsed:.6f} hits={result.hits!r}")
    assert result.verdict == "allowed" and result.fix_strategy_final == "suppress"
    assert result.hits == (
        PolicyHit(
            0,
            "CMakeLists.txt",
            "wno_flag",
            "-Wno-unused-variable",
            "target_private",
            "suppress",
            2000,
        ),
    )
    assert elapsed < 5


@pytest.mark.parametrize("depth", [64, 65, 2000])
def test_review2_genex_depth(repo, depth):
    expression = "$<1:" * depth + "-Wno-x" + ">" * depth
    result = _evaluate(repo, f'target_compile_options(t PRIVATE "{expression}")\n')
    if depth == 64:
        assert (result.verdict, result.fix_strategy_final) == ("allowed", "suppress")
        assert result.hits == (
            PolicyHit(0, "CMakeLists.txt", "wno_flag", "-Wno-x", "target_private", "suppress", 1),
        )
    else:
        assert result.verdict == "forbidden" and result.fix_strategy_final is None
        assert len(result.hits) == 1
        assert result.hits[0].kind == "cmake_genex_unparsed"
        with pytest.raises(ValueError, match="^generator expression too deep$"):
            policy_module._genex_outputs(expression, frozenset())


@pytest.mark.parametrize("depth", [65, 2000])
def test_review2_genex_deep_cli(repo, depth):
    expression = "$<1:" * depth + "-Wno-x" + ">" * depth
    spec = _spec(
        [
            _whole(
                repo,
                "CMakeLists.txt",
                "# baseline\n",
                f'target_compile_options(t PRIVATE "{expression}")\n',
            )
        ]
    )
    path = repo / "edit.json"
    path.write_text(json.dumps(spec))
    root = Path(__file__).resolve().parents[2]
    env = dict(
        os.environ, PYTHONPATH=os.pathsep.join(str(p) for p in sorted(root.glob("*/scripts")))
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ci_triage",
            "suppress-policy",
            "check",
            "--edit-spec",
            str(path),
            "--src-root",
            str(repo),
        ],
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 4
    payload = json.loads(result.stdout)
    assert payload["verdict"] == "forbidden"
    assert len(payload["hits"]) == 1 and payload["hits"][0]["kind"] == "cmake_genex_unparsed"
    assert result.stderr == "REJECTED_SUPPRESS_POLICY\n"


def test_review2_genex_recursion_error_fails_closed(repo, monkeypatch):
    def recursive(*args, **kwargs):
        raise RecursionError("fixture recursion limit")

    monkeypatch.setattr(policy_module, "_genex_outputs", recursive)
    spec = _spec(
        [
            _whole(
                repo,
                "CMakeLists.txt",
                "# baseline\n",
                "target_compile_options(t PRIVATE $<1:-Wno-x>)\n",
            )
        ]
    )
    path = repo / "edit.json"
    path.write_text(json.dumps(spec))
    stdout, stderr = io.StringIO(), io.StringIO()
    code = main(
        ["suppress-policy", "check", "--edit-spec", str(path), "--src-root", str(repo)],
        stdout=stdout,
        stderr=stderr,
    )
    assert code == 4
    result = json.loads(stdout.getvalue())
    assert result["verdict"] == "forbidden"
    assert result["hits"] and all(hit["kind"] == "cmake_genex_unparsed" for hit in result["hits"])
    assert stderr.getvalue() == "REJECTED_SUPPRESS_POLICY\n"


@pytest.mark.parametrize(
    "text,kind",
    [
        ('add_compile_options("-\\\nw")', "w_all_off"),
        (r'add_compile_options("-Wno\-everything")', "wno_wholesale"),
        ("target_compile_options(t PRIVATE PUBLIC;-Wno-unused-variable)", "wno_flag"),
        ("target_compile_options(t PRIVATE [[\nPUBLIC]] -Wno-x)", "wno_flag"),
        ('target_compile_options(t PRIVATE "$<LOWER_CASE:-W>")', "cmake_genex_unparsed"),
        ('add_compile_options("-$<1:w>")', "cmake_genex_unparsed"),
        ('add_compile_options("-W$<1:no-error>")', "cmake_genex_unparsed"),
        ('add_compile_options("$<1:->w")', "cmake_genex_unparsed"),
        ("target_compile_options(t PRIVATE -Wno-$<1:x>)", "cmake_genex_unparsed"),
        ("target_compile_options(t PRIVATE $<TARGET_FILE:x>)", "cmake_genex_unparsed"),
    ],
)
def test_review_cmake_value_rejection(repo, text, kind):
    result = _evaluate(repo, text + "\n")
    assert result.verdict == "forbidden"
    assert any(hit.kind == kind and hit.rule == "forbidden" for hit in result.hits)


def test_review_if_literal_regression(repo):
    result = _evaluate(repo, "add_compile_options($<IF:$<BOOL:1>,-w,>)\n")
    assert result.verdict == "forbidden"
    assert result.hits == (
        PolicyHit(0, "CMakeLists.txt", "w_all_off", "-w", "n/a", "forbidden", 1),
    )


@pytest.mark.parametrize(
    "text,kind",
    [
        ('add_compile_options("$<IF:$<BOOL:1>,-\\\nw,>")', "w_all_off"),
        (r'add_compile_options("$<IF:$<BOOL:1>,-Wno\-everything,>")', "wno_wholesale"),
        ("add_compile_options($<IF:$<BOOL:1>,-$<1:w>,>)", "cmake_genex_unparsed"),
    ],
)
def test_review_if_recursive_rejection(repo, text, kind):
    result = _evaluate(repo, text + "\n")
    assert result.verdict == "forbidden"
    assert any(hit.kind == kind and hit.rule == "forbidden" for hit in result.hits)


@pytest.mark.parametrize(
    "args,tokens",
    [
        ("PRIVATE -Wno-x", ["-Wno-x"]),
        ("PRIVATE $<$<C_COMPILER_ID:Clang>:-Wno-x>", ["-Wno-x"]),
        ('PRIVATE "$<$<C_COMPILER_ID:Clang>:-Wno-x;-Wno-y>"', ["-Wno-x", "-Wno-y"]),
        ('"PRIVATE" -Wno-x', ["-Wno-x"]),
        ("[[\nPRIVATE]] -Wno-x", ["-Wno-x"]),
        (r"PRIVATE -Wno\-x", ["-Wno-x"]),
        (r'PRIVATE "-Wno-x\;-Wno-y"', ["-Wno-x", "-Wno-y"]),
        ("PRIVATE $<BUILD_INTERFACE:$<1:-Wno-x>>", ["-Wno-x"]),
        ("PRIVATE $<IF:$<BOOL:1>,-Wno-x,-Wno-y>", ["-Wno-x", "-Wno-y"]),
    ],
)
def test_review_cmake_value_allowed(repo, args, tokens):
    result = _evaluate(repo, f"target_compile_options(t {args})\n# $<LOWER_CASE:-W>\n")
    assert result.verdict == "allowed"
    assert [hit.token for hit in result.hits] == tokens
    assert all(hit.scope == "target_private" for hit in result.hits)


@pytest.mark.parametrize(
    "expression",
    [
        "$<0:$<LOWER_CASE:-W>>",
        "$<$<LOWER_CASE:x>:-Wno-x>",
        "$<IF:$<BOOL:1>,-$<1:w>,>",
        "$<1:-Wno-x>$<1:-Wno-y>",
        "$<1:-Wno-x",
        "$<BOOL:$<TARGET_PROPERTY:x>>",
        "$<IF:1,-Wno-x>",
    ],
)
def test_review_genex_nested_closed_rules(repo, expression):
    result = _evaluate(repo, f'target_compile_options(t PRIVATE "{expression}")\n')
    assert result.verdict == "forbidden"
    assert result.hits[0].kind == "cmake_genex_unparsed"


@pytest.mark.parametrize("prefix", ["0xFFFF'FFFF", "1'000", "0b1010'1010", "#if 0\ndon't\n#endif"])
@pytest.mark.parametrize(
    "pragma,verdict,final",
    [
        ('#pragma GCC diagnostic ignored "-Wall"', "forbidden", None),
        ("#pragma GCC system_header", "forbidden", None),
        ("__pragma(x)", "forbidden", None),
        ('#pragma clang diagnostic ignored "-Wunused-variable"', "allowed", "suppress"),
    ],
)
def test_review_source_apostrophes(repo, prefix, pragma, verdict, final):
    result = _evaluate(repo, prefix + "\n" + pragma + "\n", file="source.cpp")
    assert (result.verdict, result.fix_strategy_final) == (verdict, final)
    assert result.hits


@pytest.mark.parametrize(
    "text",
    [
        '0xFF\'FF; _Pragma("GCC system_header")',
        "\ufeff#pragma GCC system_header",
        "%:pragma GCC system_header",
        "\v#pragma GCC system_header",
        "\f#pragma GCC system_header",
    ],
)
def test_review_pragma_prefixes_and_inline_separator(repo, text):
    result = _evaluate(repo, text + "\n", file="source.cpp")
    assert result.verdict == "forbidden"
    assert result.hits[0].kind == "pragma_wholesale"


@pytest.mark.parametrize(
    "text",
    [
        r"char c = '\'';",
        '// 0xFF\'FF; _Pragma("GCC system_header")',
        r"""const char *s = "0xFF'FF; _Pragma(\"GCC system_header\")";""",
        "/* \ufeff%:pragma GCC system_header */",
    ],
)
def test_review_source_apostrophe_near_misses(repo, text):
    assert _evaluate(repo, text + "\n", file="source.cpp").hits == ()


def test_review_symlink_category_and_grouping(repo):
    (repo / "CMakeLists.txt").write_text("# baseline\n")
    (repo / "AUTHORS.md").symlink_to("CMakeLists.txt")
    result = evaluate(
        _spec([dict(file="AUTHORS.md", old="# baseline", new="add_compile_options(-w)")]),
        repo,
        "generated",
    )
    assert result.verdict == "forbidden"
    assert result.hits[0].file == "AUTHORS.md"
    assert result.hits[0].kind == "w_all_off"


def test_review_alias_overlap(repo):
    (repo / "CMakeLists.txt").write_text("# baseline\n")
    (repo / "alias.cmake").symlink_to("CMakeLists.txt")
    edits = [
        dict(file=name, old="# baseline", new="# other")
        for name in ("alias.cmake", "CMakeLists.txt")
    ]
    result = evaluate(_spec(edits), repo, "generated")
    assert result.hits == (
        PolicyHit(
            0, "alias.cmake", "alias_overlap", "CMakeLists.txt alias.cmake", "n/a", "forbidden", 1
        ),
    )
    assert result.verdict == "forbidden"


def test_review_alias_nonoverlap_and_real_docs(repo):
    (repo / "CMakeLists.txt").write_text("add_compile_options(-Werror)\n# second\n")
    (repo / "alias.cmake").symlink_to("CMakeLists.txt")
    edits = [
        dict(file="alias.cmake", old="add_compile_options(-Werror)", new="# move"),
        dict(file="CMakeLists.txt", old="# second", new="add_compile_options(-Werror)"),
    ]
    assert evaluate(_spec(edits), repo, "generated").hits == ()
    (repo / "README.md").write_text("before")
    (repo / "alias.txt").symlink_to("README.md")
    assert (
        evaluate(_spec([dict(file="alias.txt", old="before", new="-w")]), repo, "generated").hits
        == ()
    )


def test_review_guard_location_equivalence(repo, monkeypatch):
    from tizen_build_verify import edit_spec_guard as guard

    (repo / "CMakeLists.txt").write_text("# first\n# repeated\n# repeated\n")
    spec = _spec(
        [
            dict(file="CMakeLists.txt", old="# first", new="# longer first"),
            dict(file="CMakeLists.txt", old="# repeated", new="# last", line=3),
        ]
    )
    expected, actual = [], []
    locate = guard._locate_edit

    def record(target, bucket):
        def call(*args):
            found = target(*args)
            bucket.append((str(found.file_path), found.start, found.end))
            return found

        return call

    monkeypatch.setattr(guard, "_locate_edit", record(locate, expected))
    guard.validate_edit_spec(spec, str(repo))
    monkeypatch.setattr(guard, "_locate_edit", locate)
    monkeypatch.setattr(policy_module, "_locate_edit", record(locate, actual))
    assert evaluate(spec, repo, "generated").verdict == "allowed"
    assert expected == actual
    assert json.dumps(expected).encode() == json.dumps(actual).encode()


def test_review_policy_version(repo):
    assert _evaluate(repo, "# changed\n").rules_version == "p5-policy/v2"


@pytest.mark.parametrize(
    "text,tokens",
    [
        ("-Wno-x\\", ["-Wno-x"]),
        ("'-Wno-x'", ["-Wno-x"]),
        ('"-Wno-x"', ["-Wno-x"]),
        ("${FLAGS}-Wno-x", ["-Wno-x"]),
        ("-Wno-x,-Wno-y", ["-Wno-x", "-Wno-y"]),
        ("$<$<BOOL:1>:-Wno-x>", ["-Wno-x"]),
        ("-Wno-#pragma-messages", ["-Wno-#pragma-messages"]),
        ("XX-Wno-x", []),
    ],
)
def test_token_boundaries(repo, text, tokens):
    result = _evaluate(repo, text, file="flags.txt")
    assert [hit.token for hit in result.hits] == tokens


@pytest.mark.parametrize(
    "token,kind,rule",
    [
        ("-Wno-foo", "wno_flag", "suppress"),
        ("-Wno-error=foo", "wno_error_flag", "suppress"),
        ("-Wno-error=unused-variable", "wno_error_flag", "suppress"),
        ("-Wno-error", "wno_error_all", "forbidden"),
        ("-Wno-everything", "wno_wholesale", "forbidden"),
        ("-Wno-all", "wno_wholesale", "forbidden"),
        ("-Wno-extra", "wno_wholesale", "forbidden"),
        ("-Wno-pedantic", "wno_wholesale", "forbidden"),
        ("-Wno-error=everything", "wno_wholesale", "forbidden"),
        ("-Wno-error=all", "wno_wholesale", "forbidden"),
        ("-Wno-error=extra", "wno_wholesale", "forbidden"),
        ("-Wno-error=pedantic", "wno_wholesale", "forbidden"),
        ("-w", "w_all_off", "forbidden"),
    ],
)
def test_option_kinds(repo, token, kind, rule):
    result = _evaluate(repo, f"target_compile_options(t PRIVATE {token})\n")
    scope = "target_private" if rule == "suppress" else "n/a"
    assert result.hits == (PolicyHit(0, "CMakeLists.txt", kind, token, scope, rule, 1),)
    assert result.verdict == ("allowed" if rule == "suppress" else "forbidden")
    assert result.fix_strategy_final == ("suppress" if rule == "suppress" else None)
    unchanged = _evaluate(repo, "# added comment\n" + token, "flags.txt", before=token)
    assert unchanged.hits == ()


@pytest.mark.parametrize("token", ["-Wno-error", "-Wno-everything", "-w"])
def test_wholesale_options_have_no_scope_key(repo, token):
    result = _evaluate(
        repo,
        f"add_compile_options({token})\n",
        before=f"target_compile_options(t PRIVATE {token})\n",
    )
    assert result.hits == ()
    assert result.verdict == "allowed"


@pytest.mark.parametrize(
    "text,kind,token",
    [
        ('#pragma GCC diagnostic warning "-Wunused"', "pragma_suppress", "-Wunused"),
        ('#pragma clang diagnostic ignored "-Wx"', "pragma_suppress", "-Wx"),
        ('#pragma clang diagnostic ignored \\\n "-Wx"', "pragma_suppress", "-Wx"),
        (
            '_Pragma("GCC diagnostic ignored \\"-Wunused-variable\\"")',
            "pragma_suppress",
            "-Wunused-variable",
        ),
        ('#pragma GCC diagnostic ignored "-Wall"', "pragma_wholesale", "-Wall"),
        ('#pragma clang diagnostic warning "-Wextra"', "pragma_wholesale", "-Wextra"),
        ('#pragma GCC diagnostic ignored "-Weverything"', "pragma_wholesale", "-Weverything"),
        ('#pragma GCC diagnostic ignored "-Wpedantic"', "pragma_wholesale", "-Wpedantic"),
        ("#pragma GCC system_header", "pragma_wholesale", "system_header"),
        ('_Pragma("GCC system_header")', "pragma_wholesale", "system_header"),
        ('_Pragma(STR("GCC diagnostic ignored -Wx"))', "pragma_unparsed", None),
        ("__pragma(warning(disable:4996))", "pragma_unparsed", None),
        ("#pragma GCC diagnostic ignored -Wx", "pragma_unparsed", None),
        ('_Pragma("clang diagnostic ignored \\42-Wunused\\42")', "pragma_unparsed", None),
        ("#pragma unusual diagnostic nonsense", "pragma_unparsed", None),
    ],
)
def test_pragma_kinds(repo, text, kind, token):
    result = _evaluate(repo, text + "\n", file="source.c")
    assert len(result.hits) == 1
    hit = result.hits[0]
    assert hit.kind == kind
    assert hit.token == (text if token is None else token)
    assert hit.scope == "source_local"
    assert hit.rule == ("suppress" if kind == "pragma_suppress" else "forbidden")
    assert (hit.edit_index, hit.count) == (0, 1)


@pytest.mark.parametrize(
    "text",
    [
        '_Pragma("once")',
        "#pragma once",
        "#pragma pack(push, 1)",
        "#pragma GCC diagnostic push",
        "#pragma GCC diagnostic pop",
        '#pragma GCC diagnostic error "-Wx"',
        'const char *s = "#pragma GCC diagnostic ignored \\"-Wx\\" -Wno-x";',
        '// #pragma GCC diagnostic ignored "-Wx"\nint x;',
        '/* _Pragma("GCC system_header") */ int x;',
        "char x = '\"'; // -Wno-x\n",
        'const char *s = R"tag(" __pragma(x)\n#pragma GCC system_header\n)tag";',
        "// comment \\\n#pragma GCC system_header\nint x;",
    ],
)
def test_source_near_misses(repo, text):
    assert _evaluate(repo, text, file="source.cpp").hits == ()


@pytest.mark.parametrize(
    "command,scope",
    [
        ("target_compile_options(t PRIVATE -Wno-x)", "target_private"),
        ("target_compile_options(${T} PRIVATE -Wno-x)", "target_private"),
        ("TARGET_COMPILE_OPTIONS(t PRIVATE -Wno-x)", "target_private"),
        ("target_compile_options(t PUBLIC -Wno-x)", "global_or_ambiguous"),
        ("target_compile_options(t INTERFACE -Wno-x)", "global_or_ambiguous"),
        ("target_compile_options(t -Wno-x)", "global_or_ambiguous"),
        ("target_compile_options(t PRIVATE -O2 PUBLIC -Wno-x)", "global_or_ambiguous"),
        ("target_compile_options(t PUBLIC -O2 PRIVATE -Wno-x)", "target_private"),
        ("target_compile_options(t PRIVATE -O2 INTERFACE -Wno-x)", "global_or_ambiguous"),
        ('target_compile_options(t PRIVATE -O2 "PUBLIC" -Wno-x)', "global_or_ambiguous"),
        ("target_compile_options(t PRIVATE -O2 [=[INTERFACE]=] -Wno-x)", "global_or_ambiguous"),
        ('target_compile_options(t "PRIVATE" -Wno-x)', "target_private"),
        ('target_compile_options(t "PRI\\VATE" -Wno-x)', "target_private"),
        ("target_compile_options(t PRIVATE ${MY_FLAGS} -Wno-x)", "global_or_ambiguous"),
        ("target_compile_options(t PRIVATE ${P}-Wno-x)", "global_or_ambiguous"),
        ("target_compile_options(t PRIVATE $ENV{FLAGS} -Wno-x)", "global_or_ambiguous"),
        ("target_compile_options(t PRIVATE $CACHE{FLAGS} -Wno-x)", "global_or_ambiguous"),
        ("target_compile_options(t PRIVATE $<$<C_COMPILER_ID:Clang>:-Wno-x>)", "target_private"),
        ('target_compile_options(t PRIVATE "-Wno-x")', "target_private"),
        ("target_compile_options(t PRIVATE [==[-Wno-x # ()]==])", "target_private"),
        ('target_compile_options(t PRIVATE "-Wno-x # ()")', "target_private"),
        ('set_source_files_properties(a.c PROPERTIES COMPILE_OPTIONS "-Wno-x")', "target_property"),
        ("set_target_properties(t PROPERTIES COMPILE_FLAGS -Wno-x)", "target_property"),
        ("set_property(TARGET t PROPERTY COMPILE_OPTIONS -Wno-x)", "target_property"),
        ("set_property(SOURCE a.c PROPERTY COMPILE_FLAGS -Wno-x)", "target_property"),
        ("set_property(GLOBAL PROPERTY COMPILE_OPTIONS -Wno-x)", "global_or_ambiguous"),
        ("set_target_properties(t PROPERTIES OTHER -Wno-x)", "global_or_ambiguous"),
        (
            "set_target_properties(t PROPERTIES COMPILE_OPTIONS x PROPERTIES OTHER -Wno-x)",
            "global_or_ambiguous",
        ),
        ("set_target_properties(t PROPERTIES COMPILE_OPTIONS x OTHER -Wno-x)", "target_property"),
        ('add_compile_options("-Wno-x")', "global_or_ambiguous"),
        ("add_definitions(-Wno-x)", "global_or_ambiguous"),
        ("set(FLAGS -Wno-x)", "global_or_ambiguous"),
        ("string(APPEND FLAGS -Wno-x)", "global_or_ambiguous"),
        ("list(APPEND FLAGS -Wno-x)", "global_or_ambiguous"),
        ("unknown(-Wno-x)", "global_or_ambiguous"),
        ("-Wno-x", "global_or_ambiguous"),
    ],
)
def test_cmake_scopes(repo, command, scope):
    result = _evaluate(repo, command)
    assert len(result.hits) == 1
    assert (result.hits[0].scope, result.hits[0].token) == (scope, "-Wno-x")
    assert result.verdict == ("forbidden" if scope == "global_or_ambiguous" else "allowed")


@pytest.mark.parametrize(
    "text",
    [
        "# target_compile_options(t PUBLIC -Wno-x)",
        "#[[ add_compile_options(-Wno-x) ]] set(X x)",
        "#[==[ -Wno-x add_executable(fake x) ]==]\nset(X x)",
        "target_compile_options(t PRIVATE -O2 # -Wno-x\n)",
    ],
)
def test_cmake_comments(repo, text):
    assert _evaluate(repo, text).hits == ()


@pytest.mark.parametrize(
    "prefix,operator",
    [
        ("foo", "="),
        ("foo", "+="),
        ("foo", ":="),
        ("foo", "?="),
        ("foo-bar", "="),
        ("foo.bar", "="),
        ("AM", "="),
        ("", "="),
    ],
)
def test_automake_assignment(repo, prefix, operator):
    text = f"{prefix}_CFLAGS {operator} \\\n -Wno-x # -Wno-y\n"
    result = _evaluate(repo, text, file="Makefile.am")
    assert [hit.token for hit in result.hits] == ["-Wno-x"]
    assert result.verdict == ("allowed" if prefix and prefix != "AM" else "forbidden")


@pytest.mark.parametrize(
    "file,after,expected",
    [
        ("pkg.spec", "foo_CFLAGS = -Wno-x", "forbidden"),
        ("packaging/source.c", "FLAGS = -Wno-x", "forbidden"),
        ("CMakeLists.txt", "target_compile_options(t PRIVATE -Wno-x)", "allowed"),
        ("foo.CMAKE", "target_compile_options(t PRIVATE -Wno-x)", "allowed"),
        ("Makefile.am", "foo_CXXFLAGS = -Wno-x", "allowed"),
        ("Makefile.foo", "foo_CFLAGS = -Wno-x", "forbidden"),
        ("meson.build", "-Wno-x", "forbidden"),
        ("configure", "-Wno-x", "forbidden"),
        ("foo.mk", "-Wno-x", "forbidden"),
        ("foo.in", "-Wno-x", "forbidden"),
        ("foo.ac", "-Wno-x", "forbidden"),
        ("foo.m4", "-Wno-x", "forbidden"),
        ("README.md", "explain -Wno-x", "allowed"),
        ("README.flags", "-Wno-x", "allowed"),
        ("ChangeLog", "-Wno-x", "allowed"),
        ("NEWS", "-Wno-x", "allowed"),
        ("AUTHORS", "-Wno-x", "allowed"),
        ("docs/flags.txt", "-Wno-x", "allowed"),
        ("doc/flags", "-Wno-x", "allowed"),
        ("foo.rst", "-Wno-x", "allowed"),
        ("foo.adoc", "-Wno-x", "allowed"),
        ("notes.txt", "-Wno-x", "forbidden"),
        ("unknown", "-Wno-x", "forbidden"),
        ("x.CPP", 'const char *s="-Wno-x";', "allowed"),
        ("docs/foo.mk", "-Wno-x", "forbidden"),
        ("docs/CMakeLists.txt", "add_compile_options(-Wno-x)", "forbidden"),
    ],
)
def test_file_category_precedence(repo, file, after, expected):
    assert _evaluate(repo, after, file=file).verdict == expected


@pytest.mark.parametrize(
    "before,after,kind",
    [
        ("target_compile_options(t PRIVATE -Wno-x)", "add_compile_options(-Wno-x)", "wno_flag"),
        ("# -Wno-x", "add_compile_options(-Wno-x)", "wno_flag"),
        ("add_compile_options(-Werror)", "add_compile_options(-Wno-error)", "werror_removed"),
    ],
)
def test_whole_file_migration_and_activation(repo, before, after, kind):
    result = _evaluate(repo, after, before=before)
    assert result.verdict == "forbidden"
    assert kind in [hit.kind for hit in result.hits]


def test_scope_keyword_only_edit_uses_entire_command_span(repo):
    text = "target_compile_options(t\n  PRIVATE\n  -Wno-x)\n"
    (repo / "CMakeLists.txt").write_text(text)
    result = evaluate(
        _spec([{"file": "CMakeLists.txt", "old": "PRIVATE", "new": "PUBLIC"}]), repo, "generated"
    )
    assert result.hits == (
        PolicyHit(0, "CMakeLists.txt", "wno_flag", "-Wno-x", "global_or_ambiguous", "forbidden", 1),
    )


def test_fragment_replacement_and_adjacent_edits(repo):
    (repo / "CMakeLists.txt").write_text("add_compile_options(-Werror)\n")
    result = evaluate(
        _spec([{"file": "CMakeLists.txt", "old": "error", "new": "no-error"}]), repo, "generated"
    )
    assert {hit.kind for hit in result.hits} == {"wno_error_all", "werror_removed"}
    (repo / "CMakeLists.txt").write_text("add_compile_options(LEFT_RIGHT)\n")
    result = evaluate(
        _spec(
            [
                {"file": "CMakeLists.txt", "old": "LEFT_", "new": "-Wno-"},
                {"file": "CMakeLists.txt", "old": "RIGHT", "new": "foo"},
            ]
        ),
        repo,
        "generated",
    )
    assert result.hits[0].token == "-Wno-foo"
    assert result.hits[0].edit_index == 0


@pytest.mark.parametrize("token", ["-Werror", "-Werror=unused"])
def test_same_scope_reorder_and_unchanged_suppression(repo, token):
    before = f"target_compile_options(t PRIVATE {token})\nset(X x)\n"
    after = f"set(X x)\ntarget_compile_options(t PRIVATE {token})\n"
    assert _evaluate(repo, after, before=before).hits == ()
    assert (
        _evaluate(
            repo,
            "add_compile_options(-Wno-x)\nset(X y)",
            before="add_compile_options(-Wno-x)\nset(X x)",
        ).hits
        == ()
    )


@pytest.mark.parametrize(
    "before,after,expected_count",
    [
        ("add_compile_options(-Werror)", "target_compile_options(t PRIVATE -Werror)", 1),
        ("add_compile_options(-Werror -Werror)", "set(X x)", 2),
        ("target_compile_options(t PRIVATE -Werror)", "add_compile_options(-Werror)", 0),
        (
            "target_compile_options(a PRIVATE -Werror)\ntarget_compile_options(b PRIVATE -Werror)",
            "add_compile_options(-Werror)",
            1,
        ),
        ("target_compile_options(a PRIVATE -Werror -Werror -Werror)", "set(X x)", 3),
    ],
)
def test_werror_removed_count_and_fixed_fields(repo, before, after, expected_count):
    result = _evaluate(repo, after, before=before)
    expected = (
        (
            PolicyHit(
                0, "CMakeLists.txt", "werror_removed", "-Werror", "n/a", "forbidden", expected_count
            ),
        )
        if expected_count
        else ()
    )
    assert result.hits == expected
    assert result.verdict == ("forbidden" if expected_count else "allowed")


def test_werror_removed_once_per_token_with_both_count_terms(repo):
    before = (
        "add_compile_options(-Werror -Werror=foo)\n"
        "target_compile_options(a PRIVATE -Werror -Werror -Werror=foo)\n"
    )
    result = _evaluate(repo, "set(X x)\n", before=before)
    assert result.hits == (
        PolicyHit(0, "CMakeLists.txt", "werror_removed", "-Werror", "n/a", "forbidden", 3),
        PolicyHit(0, "CMakeLists.txt", "werror_removed", "-Werror=foo", "n/a", "forbidden", 2),
    )


def test_no_cross_file_offset_for_werror_or_targets(repo):
    for text, kind in [
        ("add_compile_options(-Werror)", "werror_removed"),
        ("add_test(real COMMAND real)", "target_removed"),
    ]:
        edits = [
            _whole(repo, "strict/CMakeLists.txt", text, "# removed\n"),
            _whole(repo, "other/CMakeLists.txt", "# before\n", text),
        ]
        result = evaluate(_spec(edits), repo, "generated")
        assert result.verdict == "forbidden"
        assert [(hit.kind, hit.file) for hit in result.hits] == [(kind, "strict/CMakeLists.txt")]


@pytest.mark.parametrize(
    "command,name,new",
    [
        ("add_test", "real", "add_test(dummy COMMAND true)"),
        ("add_library", "real", "add_library(renamed real.c)"),
        ("add_executable", "real", "add_executable(renamed real.c)"),
        ("add_test", "NAME real", "add_test(NAME renamed COMMAND true)"),
        ("add_library", '"real"', "set(X x)"),
        ("add_library", "${PROJECT_NAME}", "set(X x)"),
    ],
)
def test_target_removed_fixed_fields(repo, command, name, new):
    before = f"{command}({name} COMMAND real)\n"
    result = _evaluate(repo, new, before=before)
    value = "real" if name in {'"real"', "NAME real"} else name
    assert result.hits == (
        PolicyHit(
            0, "CMakeLists.txt", "target_removed", f"{command} {value}", "n/a", "forbidden", 1
        ),
    )
    assert _evaluate(repo, "# " + before, before="# " + before).hits == ()


def test_pop_removal_fixed_fields_and_suppression_removal_offset(repo):
    before = '#pragma GCC diagnostic ignored "-Wx"\n#pragma GCC diagnostic pop\n'
    result = _evaluate(
        repo, '#pragma GCC diagnostic ignored "-Wx"\nint x;\n', file="a.c", before=before
    )
    assert result.hits == (PolicyHit(0, "a.c", "pragma_pop_removed", "pop", "n/a", "forbidden", 1),)
    assert _evaluate(repo, "int x;\n", file="a.c", before=before).hits == ()
    result = _evaluate(repo, "int x;\n", file="a.c", before=before + "#pragma GCC diagnostic pop\n")
    assert result.hits[0].count == 1


@pytest.mark.parametrize("new,count", [("", 1), (" \t\n", 1), ("/* removed */", 0)])
def test_pure_deletion_fixed_fields(repo, new, count):
    result = _evaluate(repo, new, file="unit.c", before="int unused;\n")
    assert result.hits == (
        (PolicyHit(0, "unit.c", "pure_deletion", None, "n/a", "forbidden", 1),) if count else ()
    )


@pytest.mark.parametrize(
    "source,after,expected",
    [
        ("t1_cherry_pick", "int x;", "cherry_pick"),
        ("generated", "int x;", "code"),
        ("suppress", "int x;", "suppress"),
        ("t1_cherry_pick", '#pragma GCC diagnostic ignored "-Wx"', "suppress"),
        ("t1_cherry_pick", "#pragma GCC system_header", None),
    ],
)
def test_source_kind_strategy_precedence(repo, source, after, expected):
    result = _evaluate(repo, after, file="a.c", source=source)
    assert result.fix_strategy_final == expected
    assert result.rules_version == POLICY_RULES_VERSION


@pytest.mark.parametrize("invalid", ["old_missing", "escape", "source_kind", "overlap", "schema"])
def test_policy_input_errors(repo, invalid):
    spec = _spec([_whole(repo, "a.c", "int x;\n", "int y;\n")])
    source = "generated"
    if invalid == "old_missing":
        spec["edits"][0]["old"] = "absent"
    elif invalid == "escape":
        spec["edits"][0]["file"] = "../outside.c"
    elif invalid == "source_kind":
        source = "invalid"
    elif invalid == "overlap":
        spec["edits"] *= 2
    else:
        spec["schema_version"] = "invalid"
    with pytest.raises(PolicyInputError):
        evaluate(spec, repo, source)


def test_determinism_reordering_length_changes_and_no_mutation(repo):
    path = repo / "CMakeLists.txt"
    before = "set(X old)\ntarget_compile_options(t PRIVATE -Wx)\n"
    path.write_text(before)
    edits = [
        {"file": path.name, "old": "old", "new": "much_longer_value"},
        {"file": path.name, "old": "-Wx", "new": "-Wno-x"},
    ]
    spec = _spec(edits)
    saved = copy.deepcopy(spec)
    result = evaluate(spec, repo, "generated")
    assert result == evaluate(spec, repo, "generated")
    assert spec == saved and path.read_text() == before
    assert result.hits[0].edit_index == 1
    reversed_result = evaluate(_spec(list(reversed(edits))), repo, "generated")
    assert reversed_result.hits[0].edit_index == 0
    assert [{k: v for k, v in asdict(hit).items() if k != "edit_index"} for hit in result.hits] == [
        {k: v for k, v in asdict(hit).items() if k != "edit_index"} for hit in reversed_result.hits
    ]


def test_new_span_mapping_continuations_line_anchor_and_doc_mixture(repo):
    (repo / "Makefile.am").write_text("foo_CFLAGS = -O2\nbar_CFLAGS = \\\n -Wx\n")
    edits = [
        {"file": "Makefile.am", "old": "-O2", "new": "-O3 -g -fPIC"},
        {"file": "Makefile.am", "old": "-Wx", "new": "-Wno-x", "line": 3},
    ]
    result = evaluate(_spec(edits), repo, "generated")
    assert result.hits[0].edit_index == 1
    edits = [
        _whole(repo, "README.md", "old", "explain -Wno-x"),
        _whole(repo, "unit.c", "int x;", "int y;"),
    ]
    assert evaluate(_spec(edits), repo, "generated").hits == ()


@pytest.mark.parametrize("after,exit_code", [("int y;", 0), ("#pragma GCC system_header", 4)])
def test_cli_stdout_exactly_matches_evaluate(repo, after, exit_code):
    spec = _spec([_whole(repo, "unit.c", "int x;", after)])
    path = repo / "edit.json"
    path.write_text(json.dumps(spec))
    stdout, stderr = io.StringIO(), io.StringIO()
    assert (
        main(
            ["suppress-policy", "check", "--edit-spec", str(path), "--src-root", str(repo)],
            stdout=stdout,
            stderr=stderr,
        )
        == exit_code
    )
    assert json.loads(stdout.getvalue()) == json.loads(
        json.dumps(asdict(evaluate(spec, repo, "generated")))
    )
    assert stderr.getvalue() == ("REJECTED_SUPPRESS_POLICY\n" if exit_code else "")
    assert not list(repo.glob("*.db"))


@pytest.mark.parametrize("case,expected", [("allowed", 0), ("forbidden", 4), ("invalid", 2)])
def test_cli_subprocess_exit_codes(repo, case, expected):
    spec = _spec([_whole(repo, "a.c", "int x;", "int y;" if case == "allowed" else "")])
    path = repo / "edit.json"
    path.write_text(json.dumps(spec))
    root = Path(__file__).resolve().parents[2]
    env = dict(
        os.environ, PYTHONPATH=os.pathsep.join(str(path) for path in sorted(root.glob("*/scripts")))
    )
    argv = [
        sys.executable,
        "-m",
        "ci_triage",
        "suppress-policy",
        "check",
        "--edit-spec",
        str(path),
        "--src-root",
        str(repo),
    ]
    if case == "invalid":
        argv.extend(["--source-kind", "invalid"])
    result = subprocess.run(argv, env=env, cwd=repo, text=True, capture_output=True, check=False)
    assert result.returncode == expected, result.stderr
    payload = json.loads(result.stdout)
    if case == "invalid":
        assert payload["error_code"] == "INVALID_ARGS"
    else:
        assert payload == json.loads(json.dumps(asdict(evaluate(spec, repo, "generated"))))


def test_quoted_cmake_continuation_and_unchanged_targets(repo):
    result = _evaluate(repo, 'target_compile_options(t "PRI\\\nVATE" -Wno-x)')
    assert result.hits[0].scope == "target_private"
    before = "add_library(${T} x.c)\nadd_test(NAME x COMMAND x)\n"
    assert _evaluate(repo, before + "# comment\n", before=before).hits == ()


def test_multiple_removals_use_declared_output_shape(repo):
    result = _evaluate(repo, "# removed\n", before="add_test(x COMMAND x)\n" * 3)
    assert result.hits == (
        PolicyHit(0, "CMakeLists.txt", "target_removed", "add_test x", "n/a", "forbidden", 3),
    )
    result = _evaluate(repo, "int x;\n", file="a.c", before="#pragma GCC diagnostic pop\n" * 3)
    assert result.hits == (PolicyHit(0, "a.c", "pragma_pop_removed", "pop", "n/a", "forbidden", 3),)


def test_removed_instance_old_interval_not_new_interval(repo):
    before = "set(X x)\nadd_compile_options(-Werror)\n"
    (repo / "CMakeLists.txt").write_text(before)
    result = evaluate(
        _spec(
            [
                {"file": "CMakeLists.txt", "old": "set(X x)", "new": "set(X much_longer)"},
                {"file": "CMakeLists.txt", "old": "-Werror", "new": "-O2"},
            ]
        ),
        repo,
        "generated",
    )
    assert result.hits == (
        PolicyHit(1, "CMakeLists.txt", "werror_removed", "-Werror", "n/a", "forbidden", 1),
    )


def test_sort_order_and_minimal_touching_edit(repo):
    (repo / "CMakeLists.txt").write_text("target_compile_options(t PRIVATE -Wx -Wy)\n")
    result = evaluate(
        _spec(
            [
                {"file": "CMakeLists.txt", "old": "-Wy", "new": "-Wno-y"},
                {"file": "CMakeLists.txt", "old": "-Wx", "new": "-Wno-x"},
            ]
        ),
        repo,
        "generated",
    )
    assert [hit.token for hit in result.hits] == ["-Wno-x", "-Wno-y"]
    assert [hit.edit_index for hit in result.hits] == [0, 0]


@pytest.mark.parametrize("case", ["invalid_edit", "malformed_json", "not_object", "missing_args"])
def test_cli_invalid_input_has_exit_two(repo, case):
    path = repo / "edit.json"
    path.write_text("{}")
    if case == "malformed_json":
        path.write_text("{")
    elif case == "not_object":
        path.write_text("[]")
    argv = ["suppress-policy", "check", "--edit-spec", str(path), "--src-root", str(repo)]
    if case == "missing_args":
        argv = ["suppress-policy", "check"]
    stdout, stderr = io.StringIO(), io.StringIO()
    assert main(argv, stdout=stdout, stderr=stderr) == 2
    assert json.loads(stdout.getvalue())["error_code"] == "INVALID_ARGS"
