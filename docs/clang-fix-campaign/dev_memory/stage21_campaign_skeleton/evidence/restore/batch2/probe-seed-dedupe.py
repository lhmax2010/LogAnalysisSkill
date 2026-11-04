"""Compare explicit null encodings; this probe chooses no production rule."""

from __future__ import annotations

import hashlib
import json


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    keys = (
        "package", "gerrit_path", "baseline_commit", "verified_tree_sha",
        "diagnosed_flag", "toolchain_profile", "error_signature_normalized",
    )
    seed = dict(zip(keys, (None, None, None, None, "-Wexample", "clang", "example #"), strict=True))
    try:
        "".join(seed[key] for key in keys)
    except TypeError as error:
        direct = type(error).__name__
    else:
        raise AssertionError("literal formula unexpectedly encodes null")
    empty = digest("".join(seed[key] or "" for key in keys))
    literal = digest("".join("null" if seed[key] is None else seed[key] for key in keys))
    tagged = digest("seed:" + json.dumps([seed[key] for key in keys], separators=(",", ":")))
    assert len({empty, literal, tagged}) == 3
    ordinary = dict(zip(keys, ("pkg", "platform/upstream/pkg", "a" * 40, "b" * 40,
                               "-Wexample", "clang", "example #"), strict=True))
    expected = digest("".join(ordinary[key] for key in keys))
    assert digest("".join(ordinary[key] or "" for key in keys)) == expected
    assert digest("".join("null" if ordinary[key] is None else ordinary[key]
                          for key in keys)) == expected
    print(json.dumps({
        "kind": "contract_probe_not_implementation_acceptance",
        "seed_seven_slots": seed,
        "literal_concatenation": direct,
        "candidate_hashes_not_adopted": {
            "null_to_empty": empty, "null_to_literal": literal, "tagged_json": tagged,
        },
        "ordinary_formula_sha256": expected,
        "encoding_alters_seed_identity": True,
        "production_rule_selected": False,
        "kb_or_state_db_written": False,
        "network_requests": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
