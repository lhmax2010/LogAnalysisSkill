from gbs_analyzer._utils.source_to_object import (
    build_suffix_index,
    candidates_for_source,
    is_supported_source,
    match_make_target,
    strip_ext,
)


def test_supported_source_extensions() -> None:
    assert is_supported_source("src/foo.c")
    assert is_supported_source("src/foo.cc")
    assert is_supported_source("src/foo.cpp")
    assert is_supported_source("src/foo.cxx")
    assert is_supported_source("src/foo.S")
    assert is_supported_source("src/foo.cu")


def test_unsupported_source_extension() -> None:
    assert not is_supported_source("src/foo.h")


def test_strip_ext_keeps_base_name_only() -> None:
    assert strip_ext("src/lib/foo.cc") == "foo"


def test_candidates_for_source() -> None:
    assert candidates_for_source("src/bar.cc") == {"bar.o", "bar.cc.o"}


def test_build_suffix_index_skips_unsupported_files() -> None:
    index = build_suffix_index({"src/foo.cc": "E001", "include/foo.h": "E002"})
    assert index == {"foo.o": {"E001"}, "foo.cc.o": {"E001"}}


def test_match_make_target_returns_unique_parent() -> None:
    index = build_suffix_index({"src/foo.cc": "E001"})
    assert match_make_target("build/obj/src/foo.o", index) == "E001"


def test_match_make_target_returns_none_without_match() -> None:
    assert match_make_target("bar.o", build_suffix_index({"src/foo.cc": "E001"})) is None


def test_match_make_target_returns_none_for_ambiguous_match() -> None:
    index = build_suffix_index({"src/foo.cc": "E001", "lib/foo.c": "E002"})
    assert match_make_target("obj/foo.o", index) is None
