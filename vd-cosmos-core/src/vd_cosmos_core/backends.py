"""Abstract capabilities plus saved-page readers. No HTTP client is implemented."""
from abc import ABC, abstractmethod
from datetime import datetime
import re

from .errors import FlowError, unsupported
from .export import check_content
from .files import atomic_write, confined, digest, load_json
from .models import BuildRef
from .report import normalize, parse_report
from .observation import detail_state, summarize


class Capabilities:
    capabilities = frozenset()

    def require(self, action):
        if action not in self.capabilities:
            unsupported(action)


class ReportReader(Capabilities, ABC):
    @abstractmethod
    def observe(self, build_ref): ...

    @abstractmethod
    def read_packages(self, build_ref, arch): ...

    @abstractmethod
    def read_inputs(self, build_ref): ...

    @abstractmethod
    def fetch_log(self, build_ref, arch, package): ...


class Submitter(Capabilities, ABC):
    @abstractmethod
    def prepare(self, request): ...

    @abstractmethod
    def release(self, request, intent_id): ...

    @abstractmethod
    def discover(self, mode, **kwargs): ...

    @abstractmethod
    def verify(self, request, build_ref): ...


def timestamp(value):
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if date.tzinfo is None:
            raise ValueError()
        return date.timestamp()
    except (AttributeError, ValueError):
        raise FlowError(2, "invalid_snapshot_time") from None


class SavedReportReader(ReportReader):
    """The real-format parser backend accepts saved local files only."""
    capabilities = frozenset({"observe", "read_packages", "read_inputs"})

    def __init__(self, config, manifest_path):
        self.config = config
        self.manifest_path = config.source(manifest_path)
        self.base = self.manifest_path.parent
        self.manifest = load_json(self.manifest_path)
        try:
            self.build_ref = BuildRef(**self.manifest["build_ref"])
            if self.manifest["schema_version"] != 1 or not isinstance(self.manifest["reports"], dict):
                raise ValueError()
        except (TypeError, KeyError, ValueError):
            raise FlowError(2, "invalid_fixture_manifest") from None

    def check_ref(self, build_ref):
        if build_ref != self.build_ref:
            raise FlowError(6, "build_identity_mismatch")

    def read_source(self, relative):
        try:
            path = confined(self.base, relative)
            content = path.read_bytes()
        except OSError:
            raise FlowError(5, "saved_source_unreadable") from None
        checks = check_content(content, self.config)
        if not checks["allowed"]:
            raise FlowError(4, "credential_pattern_blocked", hits=checks["credential_hits"])
        return path, content

    def _arch(self, arch):
        snapshots = self.manifest["reports"].get(arch, [])
        if not snapshots:
            return {"arch": arch, "report_state": "未知", "result_state": "未知",
                    "issues": ["no_snapshot"], "headers": {}}
        latest = snapshots[-1]
        if latest.get("status_code") == 404 and latest.get("host_ok") is True:
            return {"arch": arch, "report_state": "未发布", "result_state": "未知",
                    "issues": ["confirmed_404"], "headers": {}, "observed_at": latest["observed_at"]}
        if latest.get("status_code") != 200 or latest.get("error"):
            raise FlowError(5, "report_observation_failed")
        path, content = self.read_source(latest["path"])
        stable = False
        previous_sha = None
        if len(snapshots) >= 2 and snapshots[-2].get("status_code") == 200 and not snapshots[-2].get("error"):
            _, previous = self.read_source(snapshots[-2]["path"])
            previous_sha = digest(previous)
            stable = (previous_sha == digest(content) and
                      timestamp(latest["observed_at"]) - timestamp(snapshots[-2]["observed_at"]) >= self.config.raw["poll"]["interval_s"])
        expected = self.manifest.get("expected_packages", {}).get(arch)
        try:
            parsed = parse_report(content.decode("utf-8"), arch, self.config.raw["cosmos"], expected,
                                  stable=stable, source_url=latest.get("source_url", ""))
        except (UnicodeError, KeyError, TypeError):
            raise FlowError(5, "report_parse_failed") from None
        parsed.update({"observed_at": latest["observed_at"],
                       "evidence": {"path": str(path), "sha256": digest(content),
                                    "previous_sha256": previous_sha}})
        previous_titles = self.manifest.get("previous_table_titles", {}).get(arch, {})
        for kind, title in parsed["raw_table_titles"].items():
            if kind in previous_titles and previous_titles[kind] != title:
                parsed["issues"].append("table_title_drift:" + kind)
        return parsed

    def observe(self, build_ref):
        self.check_ref(build_ref)
        cosmos = self.config.raw["cosmos"]
        arches = cosmos["archs"]
        reports, failures = {}, []
        for arch in arches:
            try:
                reports[arch] = self._arch(arch)
            except FlowError as error:
                if error.code != 5:
                    raise
                failures.append(arch)
                # A failed observation contributes no execution/report status.
                reports[arch] = {"arch": arch, "observation_failed": True,
                                 "error": error.reason, "headers": {}, "issues": [error.reason]}
        execution = {"state": "未知", "source": None, "trust": "unknown"}
        status_source = cosmos.get("status_source")
        detail = self.manifest.get("detail_page")
        if status_source and detail:
            detail_path, data = self.read_source(detail)
            execution = {**detail_state(data, status_source), "source": str(detail_path), "sha256": digest(data)}
        return summarize(build_ref, cosmos, reports, execution, backend=self.__class__.__name__)

    def read_packages(self, build_ref, arch):
        self.check_ref(build_ref)
        if arch not in self.config.raw["cosmos"]["archs"]:
            raise FlowError(2, "unexpected_architecture")
        return self._arch(arch)

    def read_inputs(self, build_ref):
        observed = self.observe(build_ref)
        return {"header_consistency": observed["header_consistency"], "package_coverage": observed["package_coverage"],
                "reports": {a: {"headers": r.get("headers", {}), "rows": r.get("input_rows", [])}
                            for a, r in observed["reports"].items()},
                "todos": observed["todos"], "exit_code": observed["exit_code"]}

    def fetch_log(self, build_ref, arch, package):
        self.check_ref(build_ref)
        self.require("fetch_log")

    def provides(self):
        result = []
        for item in self.manifest.get("provides_evidence", []):
            path, data = self.read_source(item["path"])
            if digest(data) != item["sha256"]:
                raise FlowError(4, "provides_evidence_digest_mismatch")
            if item["source_kind"] == "spec":
                values = [normalize(m[1]) for m in re.finditer(r"^Provides\s*:\s*(.+)$", data.decode(), re.M | re.I)]
                values = [v for v in values if "%" not in v]
            elif item["source_kind"] == "rpm_metadata":
                parsed = load_json(path)
                values = parsed["provides"]
                if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
                    raise FlowError(4, "invalid_provides_metadata")
            else:
                raise FlowError(4, "unsupported_provides_source")
            result.append({"key": item["key"], "source_kind": item["source_kind"],
                           "sha256": digest(data), "evidence_path": str(path),
                           "verified": True, "provides": values})
        return result


class FixtureReportReader(SavedReportReader):
    capabilities = SavedReportReader.capabilities | {"fetch_log"}

    def fetch_log(self, build_ref, arch, package):
        self.check_ref(build_ref)
        for entry in self.manifest.get("logs", []):
            if entry["key"] == package["key"] and entry["key"]["arch"] == arch:
                _, content = self.read_source(entry["path"])
                if entry.get("sha256") and digest(content) != entry["sha256"]:
                    raise FlowError(4, "log_digest_mismatch")
                identity = digest(str(sorted(build_ref.to_dict().items())).encode())
                name = digest(str(sorted(package["key"].items())).encode())
                return atomic_write(self.config.data_root, f"rounds/{identity}/logs/{name}.txt", content)
        raise FlowError(5, "fixture_log_missing")
