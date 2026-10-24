"""Command classes are misuse guards, not isolation from the same OS account."""
from dataclasses import dataclass
from enum import Enum

from .errors import FlowError


class Category(str, Enum):
    OBSERVE = "观察"
    GENERATE = "生成分析产物"
    ACCEPT = "接收分析结果"
    HUMAN = "人工裁决"
    EXTERNAL = "外部写操作"


COMMANDS = {
    **{name: Category.OBSERVE for name in (
        "watch.observe", "fetch.packages", "fetch.inputs", "fetch.logs", "fetch.groups",
        "core.export", "core.prepush", "core.status")},
    "analyze.prepare": Category.GENERATE,
    "analyze.accept": Category.ACCEPT,
    **{name: Category.HUMAN for name in (
        "confirm", "confirm-group", "confirm-bug", "confirm-terminal", "approve",
        "attest", "resolve", "bind", "rebind", "parse-override", "round.abandon")},
    **{name: Category.EXTERNAL for name in ("submit", "p4.create-cl", "p4.shelve")},
}
EVENTS = {
    Category.OBSERVE: {"observation_started", "observation_recorded", "observation_failed",
                       "artifact_recorded", "inbox_opened", "fetch_started", "fetch_completed"},
    Category.GENERATE: {"analysis_prepared"},
    Category.ACCEPT: {"analysis_received", "analysis_rejected"},
    Category.HUMAN: {"confirmed", "approved", "terminal_confirmed", "attested", "resolved",
                     "bind", "rebind", "parse_overridden", "round_abandoned"},
    Category.EXTERNAL: {"submit_session_started", "submit_session_finished", "click_intent",
                        "submit_result", "p4_operation_started", "p4_operation_result"},
}


@dataclass(frozen=True)
class CommandContext:
    name: str
    category: Category
    terminal_confirmed: bool = False


def command_context(name):
    if name not in COMMANDS:
        raise FlowError(2, "unregistered_command")
    category = COMMANDS[name]
    confirmed = False
    if category in {Category.HUMAN, Category.EXTERNAL}:
        try:
            with open("/dev/tty", "r+", encoding="utf-8") as tty:
                if not tty.isatty():
                    raise FlowError(2, "terminal_required")
                tty.write("Confirm command (yes): ")
                tty.flush()
                confirmed = tty.readline().strip() == "yes"
        except OSError:
            raise FlowError(2, "terminal_required") from None
        if not confirmed:
            raise FlowError(3, "confirmation_required")
    return CommandContext(name, category, confirmed)


def authorize_event(context, kind):
    if not isinstance(context, CommandContext) or COMMANDS.get(context.name) != context.category:
        raise FlowError(4, "invalid_command_context")
    if kind not in EVENTS[context.category]:
        raise FlowError(4, "event_not_authorized")
    if context.category in {Category.HUMAN, Category.EXTERNAL} and not context.terminal_confirmed:
        raise FlowError(2, "terminal_required")
