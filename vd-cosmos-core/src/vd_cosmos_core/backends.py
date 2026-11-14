"""Abstract capabilities and local saved-page/fixture readers."""
from .dates import parse_datetime
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
import re

from .errors import FlowError, unsupported
from .export import check_content
from .files import atomic_write, confined, digest, load_json, json_bytes
from .versions import build_key, parsing_digest
from .stability import advance, maturity, execution_clock
from .receipts import terminal_basis, log_binding, manual_terminal
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
        date = parse_datetime(value)
        if date.tzinfo is None:
            raise ValueError()
        return date.timestamp()
    except (AttributeError, ValueError):
        raise FlowError(2, "invalid_snapshot_time") from None


class SavedReportReader(ReportReader):
    """The real-format parser backend accepts saved local files only."""
    capabilities = frozenset({"observe", "read_packages", "read_inputs"})

    def __init__(self, config, manifest_path):
        self._observed = None
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

    def expected_digest(self):
        return digest(json_bytes(self.manifest.get("expected_packages")))

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

    def _arch(self, arch, execution):
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
        record, previous_sha, timing = None, None, {}
        for snapshot in snapshots:
            if snapshot.get('status_code') != 200 or snapshot.get('error'):
                record = None
                continue
            _, raw = self.read_source(snapshot['path'])
            previous_sha = record['sha256'] if record else None
            timing = execution_clock(timing, execution, snapshot['observed_at'], report_success=True)
            record = advance(record, digest(raw), snapshot['observed_at'], parsing_digest(self.config), timing)
        stable, settled = maturity(record, self.config.raw['poll'], timing)
        expected = self.manifest.get("expected_packages", {}).get(arch)
        try:
            parsed = parse_report(content.decode("utf-8"), arch, self.config.raw["cosmos"], expected,
                                  stable=stable, settled=settled, source_url=latest.get("source_url", ""))
        except (UnicodeError, KeyError, TypeError):
            raise FlowError(5, "report_parse_failed") from None
        execution.update(timing)
        execution["terminal_basis"] = terminal_basis(execution)
        parsed.update({"continuous": record, "settled_basis": record["settled_basis"], "observed_at": latest["observed_at"],
                       "evidence": {"path": str(path), "sha256": digest(content),
                                    "previous_sha256": previous_sha}})
        previous_titles = self.manifest.get("previous_table_titles", {}).get(arch, {})
        for kind, title in parsed["raw_table_titles"].items():
            if kind in previous_titles and previous_titles[kind] != title:
                parsed["issues"].append("table_title_drift:" + kind)
        return parsed

    def observe(self, build_ref):
        self.check_ref(build_ref)
        if self._observed is not None:
            return self._observed
        cosmos = self.config.raw["cosmos"]
        execution = {"state": "未知", "trust": "unknown", "basis": "title_not_matched"}
        status_source, detail = cosmos.get('status_source'), self.manifest.get('detail_page')
        if status_source and detail:
            try:
                detail_path, data = self.read_source(detail)
                execution = {**detail_state(data, status_source, self.build_ref.run_id),
                             "source": str(detail_path), "sha256": digest(data), "detail_attempted": True}
            except FlowError as error:
                if error.code != 5:
                    raise
                execution = {"state": "未知", "trust": "unknown", "basis": "detail_fetch_failed", "failure": error.reason, "detail_attempted": True}
        arches = cosmos["archs"]
        reports, failures = {}, []
        for arch in arches:
            try:
                reports[arch] = self._arch(arch, execution)
            except FlowError as error:
                if error.code != 5:
                    raise
                failures.append(arch)
                # A failed observation contributes no execution/report status.
                reports[arch] = {"arch": arch, "observation_failed": True,
                                 "error": error.reason, "headers": {}, "issues": [error.reason]}
        state_path = self.config.output('rounds/' + build_key(self) + '/fixture-detail.json')
        previous = load_json(state_path) if state_path.exists() else {}
        invalidated = previous.get('invalid_manual_events', [])
        manual = manual_terminal(self.config, build_key(self), reports, invalidated)
        execution['terminal_basis'] = terminal_basis(execution, manual)
        execution['manual_conflict'] = bool(manual and execution.get('effective_state') in {'运行', '排队'})
        if manual:
            for arch, report in list(reports.items()):
                if not report.get('continuous'):
                    continue
                stable, settled = maturity(report['continuous'], self.config.raw['poll'], execution, manual)
                raw = parse_report(Path(report['evidence']['path']).read_text(), arch, cosmos,
                    self.manifest.get('expected_packages', {}).get(arch), stable=stable, settled=settled,
                    source_url=self.manifest['reports'][arch][-1].get('source_url', ''))
                raw.update({k: report[k] for k in ('continuous', 'observed_at', 'evidence')})
                raw['settled_basis'] = report['continuous']['settled_basis']
                reports[arch] = raw
        atomic_write(self.config.data_root, state_path, json_bytes({'invalid_manual_events': invalidated}))
        self._observed = summarize(build_ref, cosmos, reports, execution, backend=self.__class__.__name__)
        return self._observed

    def read_packages(self, build_ref, arch):
        self.check_ref(build_ref)
        if arch not in self.config.raw["cosmos"]["archs"]:
            raise FlowError(2, "unexpected_architecture")
        return self.observe(build_ref)["reports"][arch]

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
                identity = build_key(self)
                name = digest(str(sorted(package["key"].items())).encode())
                binding = log_binding(self.observe(build_ref), arch, self.config.raw['fetch']['max_log_bytes'], entry['path'])
                revision = digest(json_bytes({'body': digest(content), 'binding': binding}))
                receipt = {**atomic_write(self.config.data_root, f"rounds/{identity}/logs/{name}/{revision}/log.txt", content),
                        'key': package['key'], 'first_failure_observed_at': self.observe(build_ref)['observed_at'],
                        'binding': binding, 'final': binding['final_stage'], 'transfer_complete': True,
                        'settled_basis': binding['settled_basis'], 'terminal_basis': binding['terminal_basis']}
                atomic_write(self.config.data_root, receipt['path'] + '.json', json_bytes(receipt))
                return receipt
        raise FlowError(5, "fixture_log_missing")
