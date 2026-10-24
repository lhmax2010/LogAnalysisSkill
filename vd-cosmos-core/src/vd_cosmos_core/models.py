"""Public, JSON-serializable identities; no network-specific globals."""
from dataclasses import asdict, dataclass, field

from .errors import FlowError


@dataclass(frozen=True)
class BuildRef:
    backend_id: str
    instance_id: str
    run_id: str
    execution_kind: str

    def __post_init__(self):
        if not all(isinstance(x, str) and x.strip() for x in (
                self.backend_id, self.instance_id, self.run_id)):
            raise FlowError(2, "invalid_build_ref")
        if self.execution_kind not in {"cosmos", "local_simulation"}:
            raise FlowError(2, "invalid_execution_kind")

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True, order=True)
class PackageKey:
    arch: str
    name: str
    path: str

    def to_dict(self):
        return asdict(self)


@dataclass
class Package:
    key: PackageKey
    version: str | None
    cl: str
    shelve: bool
    category: str
    log_url: str | None
    missing_dependencies: list[str] = field(default_factory=list)
    source_line: int = 0
    raw_path: str = ""
    raw_status: str = ""
    other_expansion_messages: list[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
