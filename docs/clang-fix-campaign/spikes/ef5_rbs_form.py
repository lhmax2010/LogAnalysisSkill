"""Offline-only inspection of a user-saved QuickBuild run form; never submit it."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path

from ef5_probe import MASK
from ef5_web_probe import SECRET_NAME, PageRedactor, _UserFields

REDACTED = "<REDACTED>"
VOID = frozenset({"area", "base", "br", "col", "embed", "hr", "img", "input",
                  "link", "meta", "param", "source", "track", "wbr"})
SECRET_VALUE = re.compile(
    r'''(?ix)[\w-]*(?:token|csrf|xsrf|session)[\w-]*["']?\s*[:=]\s*
    (?:"([^"]*)"|'([^']*)'|([^?&;\s<>"'`)\]}]+))'''
)
VALUE_ATTR = re.compile(r'''(?is)(\svalue\s*=\s*)(?:"[^"]*"|'[^']*'|[^\s>]+)''')
ACTION = re.compile(r"IFormSubmitListener|ILinkListener|IBehaviorListener|Wicket\.Ajax", re.I)
FORBIDDEN_ACTION_TOKENS = ("ILinkListener-content-buildHead-promote",)


@dataclass(eq=False)
class Node:
    tag: str
    attrs: dict[str, str]
    line: int
    start: int
    raw_tag: str
    parent: Node | None = None
    children: list[Node | str] = field(default_factory=list)

    def walk(self) -> list[Node]:
        found = [self]
        for child in self.children:
            if isinstance(child, Node):
                found.extend(child.walk())
        return found

    def text(self) -> str:
        return "".join(child.text() if isinstance(child, Node) else child
                       for child in self.children)

    def source(self) -> str:
        return f"form.redacted.html:{self.line}"


class DOM(HTMLParser):
    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.root = Node("document", {}, 1, 0, "")
        self.stack = [self.root]
        self.offsets = [0]
        for line in source.splitlines(keepends=True):
            self.offsets.append(self.offsets[-1] + len(line))
        self.feed(source)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        line, col = self.getpos()
        node = Node(tag, {k: v or "" for k, v in attrs}, line,
                    self.offsets[line - 1] + col, self.get_starttag_text() or "", self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, text: str) -> None:
        self.stack[-1].children.append(text)


class FormRedactor(PageRedactor):
    def __init__(self) -> None:
        super().__init__("", "", "")
        self.identities: set[str] = set()

    def remember(self, value: str) -> None:
        if MASK not in value and REDACTED not in unescape(value):
            super().remember(value)

    def redact(self, text: str) -> str:
        users = _UserFields(text)
        users.feed(text)
        for start, end in users.spans:
            value = DOM(text[start:end]).root.text().strip()
            if value and value != "<USER>":
                self.identities.add(value)
        for match in SECRET_VALUE.finditer(unescape(text)):
            value = next(v for v in match.groups() if v is not None)
            if value not in {REDACTED, MASK, "&lt;REDACTED&gt;"}:
                self.remember(value)
        # Hidden UI selections are not secrets elsewhere in the page. Mask their
        # attributes before PageRedactor so a value like "1" cannot erase markup.
        hidden = [n for n in DOM(text).root.walk()
                  if n.tag == "input" and n.attrs.get("type", "").lower() == "hidden"]
        for node in reversed(hidden):
            if "value" not in node.attrs:
                continue
            if SECRET_NAME.search(node.attrs.get("name", "") + node.attrs.get("id", "")):
                self.remember(node.attrs["value"])
            tag = VALUE_ATTR.sub(lambda m: m[1] + '"' + MASK + '"', node.raw_tag, count=1)
            text = text[:node.start] + tag + text[node.start + len(node.raw_tag):]
        for value in sorted(self.secrets, key=len, reverse=True):
            text = text.replace(value, MASK)
        safe = super().redact(text)
        for identity in sorted(self.identities, key=len, reverse=True):
            for spelling in {escape(identity), identity}:
                safe = re.sub(r"(?<!\w)" + re.escape(spelling) + r"(?!\w)",
                              "&lt;USER&gt;", safe)
        safe = safe.replace(MASK, "&lt;REDACTED&gt;")
        self.check_safe(safe)
        return safe

    def check_safe(self, text: str) -> None:
        self.check(text.replace("&lt;REDACTED&gt;", MASK).replace(REDACTED, MASK))
        decoded = unescape(text)
        if any(re.search(r"(?<!\w)" + re.escape(identity) + r"(?!\w)", decoded)
               for identity in self.identities):
            raise ValueError("identity redaction failed")
        for match in SECRET_VALUE.finditer(decoded):
            value = next(v for v in match.groups() if v is not None)
            if value not in {REDACTED, MASK, ""}:
                raise ValueError("session redaction failed")
        for node in DOM(text).root.walk():
            if (node.tag == "input" and node.attrs.get("type", "").lower() == "hidden"
                    and "value" in node.attrs and node.attrs["value"] != REDACTED):
                raise ValueError("hidden value redaction failed")


def ancestors(node: Node) -> list[Node]:
    result = []
    parent = node.parent
    while parent is not None:
        result.append(parent)
        parent = parent.parent
    return result


def compact(text: str) -> str:
    return " ".join(text.split())


def label_context(node: Node, nodes: list[Node]) -> tuple[Node | None, Node | None]:
    for parent in ancestors(node):
        if parent.tag == "tr":
            cells = [c for c in parent.children if isinstance(c, Node) and c.tag == "td"]
            for cell in cells:
                if "name" in cell.attrs.get("class", "").split():
                    labels = [n for n in cell.walk()
                              if "form-label" in n.attrs.get("class", "").split()]
                    if labels:
                        return labels[0], parent
        if parent.tag == "label":
            return parent, parent
    for label in nodes:
        if label.tag == "label" and label.attrs.get("for") == node.attrs.get("id"):
            return label, label
    return None, None


def action_info(value: str) -> dict[str, object]:
    listeners = sorted(set(re.findall(r"I(?:FormSubmit|Link|Behavior)Listener", value)))
    return {"value": value, "wicket_action": bool(ACTION.search(value)),
            "listeners": listeners,
            "permanently_forbidden": any(token in value for token in FORBIDDEN_ACTION_TOKENS)}


def events(node: Node) -> list[dict[str, object]]:
    result = []
    for key, value in node.attrs.items():
        if key.startswith("on"):
            urls = [match[2] for match in re.finditer(r'''(["'])(.*?)\1''', value)
                    if ACTION.search(match[2])]
            result.append({"event": key, "code": value, "source": node.source(),
                           "server_callback": bool(ACTION.search(value)),
                           "urls": [action_info(url) for url in urls],
                           "refreshed_fields": "NOT_OBSERVED_IN_SAVED_HTML"})
    return result


def options(node: Node) -> list[dict[str, object]]:
    return [{"text": option.text(), "value": option.attrs.get("value"),
             "selected": "selected" in option.attrs, "disabled": "disabled" in option.attrs,
             "source": option.source()}
            for option in node.walk() if option.tag == "option"]


def field_info(node: Node, nodes: list[Node]) -> dict[str, object]:
    label, row = label_context(node, nodes)
    markers = [n for n in (row.walk() if row else [])
               if ("required" in n.attrs.get("class", "").split()
                   or "required" in n.attrs.get("title", "").lower()) and "*" in n.text()]
    kind = node.attrs.get("type", "text").lower() if node.tag == "input" else node.tag
    option_rows = options(node)
    default: object = node.attrs.get("value")
    if node.tag == "textarea":
        default = node.text()
    elif node.tag == "select":
        default = [option["value"] for option in option_rows if option["selected"]]
    elif kind in {"checkbox", "radio"}:
        default = {"checked": "checked" in node.attrs, "value_attribute": node.attrs.get("value")}
    return {"label": compact(label.text()) if label else None,
            "label_source": label.source() if label else None,
            "source": node.source(), "html_name": node.attrs.get("name"),
            "id": node.attrs.get("id"), "type": kind,
            "palette_role": (node.attrs.get("name", "").rsplit(":palette:", 1)[1]
                             if ":palette:" in node.attrs.get("name", "") else None),
            "required_marker_observed": bool(markers) or "required" in node.attrs,
            "required_sources": [m.source() for m in markers]
            + ([node.source()] if "required" in node.attrs else []),
            "default": default, "value_attribute_present": "value" in node.attrs,
            "multiple": "multiple" in node.attrs, "disabled": "disabled" in node.attrs,
            "options": option_rows, "events": events(node)}


def palette_info(node: Node, nodes: list[Node], source: str) -> dict[str, object]:
    label, row = label_context(node, nodes)
    if row is None:
        raise ValueError("palette has no labelled row")
    prefix = node.attrs["name"].removesuffix("recorder")
    members = [n for n in row.walk() if n.attrs.get("name", "").startswith(prefix)]
    excluded = []
    for member in members:
        ident = member.attrs.get("id")
        if ident:
            pattern = r"Wicket\.Form\.excludeFromAjaxSerialization\." + re.escape(ident) + r"\s*="
            for match in re.finditer(pattern, source):
                line = source.count("\n", 0, match.start()) + 1
                excluded.append({"html_name": member.attrs.get("name"), "id": ident,
                                 "source": f"form.redacted.html:{line}"})
    return {"label": compact(label.text()) if label else None, "type": "dual-list",
            "source": node.source(), "recorder_name": node.attrs["name"],
            "recorder_value": node.attrs.get("value"),
            "recorder_events": events(node),
            "members": [{"name": n.attrs.get("name"), "id": n.attrs.get("id"),
                         "source": n.source(), "options": options(n)} for n in members],
            "excluded_from_ajax_serialization": excluded,
            "actual_submission": "NOT_PERFORMED",
            "multi_value_serialization": "NOT_OBSERVED; external palette.js was not loaded"}


def inspect_form(safe: str) -> dict[str, object]:
    nodes = DOM(safe).root.walk()
    forms = []
    for form in (n for n in nodes if n.tag == "form"):
        descendants = form.walk()
        fields = [field_info(n, nodes) for n in descendants
                  if n.tag in {"input", "select", "textarea"}]
        readonly = []
        for label in descendants:
            if "form-label" not in label.attrs.get("class", "").split():
                continue
            row = next((a for a in ancestors(label) if a.tag == "tr"), None)
            if row and not any(n.tag in {"input", "select", "textarea"} for n in row.walk()):
                cells = [c for c in row.children if isinstance(c, Node) and c.tag == "td"]
                readonly.append({"label": compact(label.text()), "source": label.source(),
                                 "value": compact(cells[-1].text()),
                                 "value_source": cells[-1].source(), "html_name": None,
                                 "type": "read_only_display"})
        forms.append({"id": form.attrs.get("id"), "source": form.source(),
                      "method": form.attrs.get("method"),
                      "action": action_info(form.attrs.get("action", "")),
                      "enctype": form.attrs.get("enctype"), "fields": fields,
                      "read_only_fields": readonly,
                      "palettes": [palette_info(n, nodes, safe) for n in descendants
                                   if n.attrs.get("name", "").endswith(":palette:recorder")]})
    buttons = []
    for node in nodes:
        if not (node.tag == "button"
                or (node.tag == "input" and node.attrs.get("type") in {"submit", "button", "reset"})
                or (node.tag == "a" and "btn" in node.attrs.get("class", "").split())):
            continue
        button_form = next((a for a in ancestors(node) if a.tag == "form"), None)
        buttons.append({"source": node.source(), "tag": node.tag,
                        "type": node.attrs.get("type"), "name": node.attrs.get("name"),
                        "value": node.attrs.get("value"), "text": compact(node.text()),
                        "title": node.attrs.get("title"), "class": node.attrs.get("class"),
                        "form_id": button_form.attrs.get("id") if button_form else None,
                        "href": action_info(node.attrs.get("href", "")), "events": events(node),
                        "form_action": action_info(button_form.attrs.get("action", ""))
                        if button_form else None})
    return {"network_requests": 0, "javascript_executed": False, "forms_submitted": 0,
            "forbidden_action_tokens": list(FORBIDDEN_ACTION_TOKENS),
            "titles": [{"text": n.text(), "source": n.source()} for n in nodes if n.tag == "title"],
            "forms": forms, "buttons": buttons,
            "external_scripts_not_loaded": [
                {"src": n.attrs["src"], "source": n.source()}
                for n in nodes if n.tag == "script" and "src" in n.attrs],
            "inline_ajax_scripts": [
                {"code": n.text(), "source": n.source()}
                for n in nodes if n.tag == "script" and ACTION.search(n.text())],
            "not_observed": ["response after submission", "how a new build ID is obtained",
                             "server-side refresh targets after field changes"]}


def archive_form(source: Path, output: Path) -> dict[str, object]:
    raw = source.read_bytes()
    redactor = FormRedactor()
    safe = redactor.redact(raw.decode("utf-8"))
    if safe.count("\n") != raw.count(b"\n"):
        raise ValueError("source line numbers changed")
    data = inspect_form(safe)
    shapes = []
    safe_nodes = DOM(safe).root.walk()
    for original in DOM(raw.decode()).root.walk():
        if not original.attrs.get("name", "").endswith(":palette:recorder"):
            continue
        value = original.attrs.get("value", "")
        node = next(n for n in safe_nodes if n.tag == "input" and n.line == original.line)
        _, row = label_context(node, safe_nodes)
        visible_options = [n for n in row.walk() if n.tag == "option"] if row else []
        is_hex = bool(re.fullmatch(r"[0-9a-fA-F]+", value)) and len(value) % 2 == 0
        shapes.append({
            "source": node.source(), "html_name": node.attrs.get("name"),
            "empty": value == "", "single_hex_value": is_hex,
            "matches_visible_option_value": any(n.attrs.get("value") == value
                                                 for n in visible_options),
            "hex_decodes_to_visible_option_text": is_hex and any(
                bytes.fromhex(value).decode("utf-8", errors="replace") == n.text()
                for n in visible_options),
            "raw_hidden_value": REDACTED,
            "multi_value_delimiter": "NOT_OBSERVED"})
    data["hidden_palette_value_shapes"] = shapes
    data["redacted_sha256"] = hashlib.sha256(safe.encode()).hexdigest()
    data["redaction_self_check"] = "PASS"
    data["identity_spans_masked"] = len(redactor.identities)
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    redactor.check(payload.replace(REDACTED, MASK))
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    for name, text in (("form.redacted.html", safe), ("form.json", payload)):
        path = output / name
        path.write_bytes(text.encode())
        path.chmod(0o600)
        if path.read_bytes() != text.encode():
            raise ValueError("write verification failed")
    redactor.check_safe((output / "form.redacted.html").read_bytes().decode())
    if source.read_bytes() != raw:
        raise ValueError("original file changed")
    forms = data["forms"]
    assert isinstance(forms, list)
    return {"network_requests": 0, "forms": len(forms),
            "redaction_self_check": "PASS", "redacted_sha256": data["redacted_sha256"],
            "original_unchanged": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    def deny_network(event: str, arguments: tuple[object, ...]) -> None:
        if event in {"socket.connect", "socket.getaddrinfo", "socket.sendto"}:
            raise RuntimeError("network is prohibited")

    sys.addaudithook(deny_network)
    try:
        report = archive_form(args.input, args.output)
    except Exception:
        print("OFFLINE_FORM_FAILED; no raw input or exception content emitted")
        return 1
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
