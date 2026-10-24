"""Scripted browser-free Submitter test double, not a submission protocol."""
from .backends import Submitter
from .errors import FlowError


class DriverCrash(RuntimeError):
    pass


class ScriptedDriver:
    def __init__(self, steps):
        self.steps = list(steps)
        self.position = 0
        self.trace = []

    def step(self, action):
        if self.position >= len(self.steps):
            raise FlowError(6, "fixture_sequence_exhausted")
        step = self.steps[self.position]
        if step["action"] != action:
            raise FlowError(6, "fixture_sequence_mismatch")
        self.position += 1
        page = step["page"]
        if page not in {"success", "rejected", "login", "unknown", "crash", "form"}:
            raise FlowError(2, "invalid_fixture_page")
        self.trace.append({"action": action, "page": page})
        if page == "crash":
            raise DriverCrash("scripted_crash")
        return step


class FixtureSubmitter(Submitter):
    capabilities = frozenset({"prepare", "release", "discover", "verify"})

    def __init__(self, driver):
        self.driver = driver
        self.prepared = set()
        self.released = set()

    def prepare(self, request):
        step = self.driver.step("prepare")
        if step["page"] == "form":
            self.prepared.add(request["request_id"])
            return {"status": "prepared", "readback": step.get("fields", {})}
        return {"status": "auth_required" if step["page"] == "login" else "not_prepared"}

    def release(self, request, intent_id):
        request_id = request["request_id"]
        if not intent_id or request_id not in self.prepared or request_id in self.released:
            raise FlowError(6, "fixture_release_precondition")
        self.released.add(request_id)
        step = self.driver.step("release")
        return {"status": {"success": "accepted", "rejected": "rejected"}.get(step["page"], "uncertain"),
                "intent_id": intent_id}

    def discover(self, mode, **kwargs):
        if mode not in {"receipt", "marker", "unmarked_candidates"}:
            raise FlowError(2, "invalid_discovery_mode")
        step = self.driver.step("discover")
        return {"mode": mode, "candidates": step.get("candidates", []) if step["page"] == "success" else [],
                "page": step["page"]}

    def verify(self, request, build_ref):
        step = self.driver.step("verify")
        return {"status": {"success": "一致", "rejected": "不一致"}.get(step["page"], "未核验")}
