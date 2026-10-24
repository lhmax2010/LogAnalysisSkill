"""Expansion signatures and evidence-backed blocking, without disposition authority."""
import re
from .report import normalize


def key_of(package):
    key = package["key"]
    return (key["arch"], key["name"], key["path"])


def group_expansion(packages, provides=()):
    failures = {key_of(p): p for p in packages if p["category"] == "build_error"}
    other = {(p["key"]["arch"], normalize(message)) for p in packages
             for message in p.get("other_expansion_messages", [])}
    verified = {}
    for entry in provides:
        key = (entry["key"]["arch"], entry["key"]["name"], entry["key"]["path"])
        if key not in failures or entry.get("source_kind") not in {"spec", "rpm_metadata"}:
            continue
        # Evidence is content-addressed and must have been verified by the reader.
        if not entry.get("verified") or not entry.get("sha256"):
            continue
        for value in entry["provides"]:
            verified.setdefault((key[0], normalize(value)), []).append((key, entry))
    groups, downstream = {}, {}
    for package in packages:
        if package["category"] != "expansion_error":
            continue
        for dependency in package["missing_dependencies"]:
            signature = normalize(dependency)
            arch = package["key"]["arch"]
            group = groups.setdefault((arch, signature), {
                "arch": arch, "signature": signature, "normalization_version": 1,
                "message_format": "其它格式" if (arch, signature) in other else "nothing provides",
                "requires_manual_confirmation": (arch, signature) in other,
                "members": [], "certain_blockers": [], "suspected_blockers": []})
            if package["key"] not in group["members"]:
                group["members"].append(package["key"])
            providers = [] if (arch, signature) in other else verified.get((arch, signature), [])
            for key, evidence in providers:
                item = {"key": failures[key]["key"], "source_kind": evidence["source_kind"],
                        "sha256": evidence["sha256"], "evidence_path": evidence["evidence_path"]}
                if item not in group["certain_blockers"]:
                    group["certain_blockers"].append(item)
                downstream.setdefault(key, set()).add(key_of(package))
            base = re.split(r"\s*[<>=]", signature)[0]
            for key in failures:
                name = key[1]
                if key[0] == arch and (base == name or base.startswith(name + "-") or name.startswith(base + "-")):
                    if any(provider[0] == key for provider in providers):
                        continue
                    item = {"key": failures[key]["key"], "basis": "name_similarity_requires_confirmation"}
                    if item not in group["suspected_blockers"]:
                        group["suspected_blockers"].append(item)
    return {"groups": [groups[k] for k in sorted(groups)],
            "blocking_downstream": [{"key": failures[k]["key"], "count": len(v)}
                                     for k, v in sorted(downstream.items())]}


def package_covered(package, groups, confirmed_signatures=(), repaired_providers=()):
    """Pure projection: caller must supply already validated, round-scoped confirmations."""
    missing = set(map(normalize, package["missing_dependencies"]))
    if not missing:
        return False
    arch = package["key"]["arch"]
    confirmed = set(confirmed_signatures)
    repaired = set(repaired_providers)
    covered = {signature for item_arch, signature in confirmed if item_arch == arch}
    for group in groups["groups"]:
        if group["arch"] != arch or group.get("requires_manual_confirmation"):
            continue
        if any((b["key"]["arch"], b["key"]["name"], b["key"]["path"]) in repaired
               for b in group["certain_blockers"]):
            covered.add(group["signature"])
    return missing <= covered
