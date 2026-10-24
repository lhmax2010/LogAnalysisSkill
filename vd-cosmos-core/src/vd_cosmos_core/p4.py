"""P4 plan-only adapter. No method in this batch launches P4."""
import os
from dataclasses import dataclass

from .errors import FlowError, unsupported


@dataclass
class P4Plan:
    argv: list[str]
    env: dict[str, str]
    cwd: str


class P4Adapter:
    def __init__(self, config):
        self.config = config

    def plan(self, args):
        if not args or not isinstance(args, list) or not all(isinstance(x, str) for x in args):
            raise FlowError(2, "invalid_p4_arguments")
        # Global CLI connection options are deliberately not accepted.
        if args[0].startswith("-"):
            raise FlowError(4, "p4_connection_options_forbidden")
        if args[0] in {"set", "login", "submit", "client"}:
            raise FlowError(4, "p4_command_forbidden")
        if args[0] not in {"print", "describe", "info", "changes", "fstat"}:
            raise FlowError(4, "p4_command_not_in_read_allowlist")
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith("P4")}
        env["P4CONFIG"] = str(self.config.output(self.config.raw["p4"]["config_file"]))
        connection = self.config.raw["p4"].get("env", {})
        if not set(connection) <= {"P4PORT", "P4USER", "P4CLIENT", "P4CHARSET"}:
            raise FlowError(4, "p4_environment_not_allowed")
        env.update(connection)
        for name, rel in (("TMPDIR", "tmp/p4"), ("XDG_CACHE_HOME", "tmp/p4-cache")):
            env[name] = str(self.config.output(rel))
        return P4Plan(["p4", *args], env, str(self.config.output("tmp/p4-work")))

    def execute(self, args):
        self.plan(args)
        unsupported("p4.execute")
