"""Registered Recent Builds structure reconstructed from the C6b archive."""

import html
from pathlib import Path
from types import SimpleNamespace

from ci_triage import qb_result_html as pages

ROOT = Path(__file__).resolve().parents[2]
CONFIG_ARCHIVE = ROOT / (
    "docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/"
    "evidence/C6b/raw-active-01/05.raw-redacted.html"
)


def configuration(profile, builds=()):
    source = pages.Document(CONFIG_ARCHIVE.read_text()).root
    # Assert the synthetic response models the observed six-column/direct-child shape.
    heading = next(
        h
        for h in source.find(cls="box-head")
        if any(
            isinstance(c, pages.Element) and c.has("flex-1") and c.text().strip() == "Recent Builds"
            for c in h.children
        )
    )
    headers = [n.text().strip() for n in heading.parent.find("table")[0].find("th")]
    assert headers == ["Id", "Version", "Master Node", "Begin Date", "Duration", "Triggered By"]
    path = profile["configuration_path"]
    crumbs = "".join(f"<span>{html.escape(segment)}</span>" for segment in path.split("/"))
    rows = "".join(
        f'<tr><td>{build}</td><td><a href="/build/{build}">Build</a>'
        '<a href="javascript:void(0);">menu</a>'
        '<a href="/?0-1.ILinkListener-stop">stop</a></td><td>main</td>'
        "<td>2026-10-21</td><td>1s</td><td>&lt;USER&gt;</td></tr>"
        for build in builds
    )
    return (
        f"<html><title>QuickBuild - {html.escape(path)}</title>"
        f'<div id="breadcrumb">{crumbs}</div>'
        f"<script>onCopyClipboardLinkDomReady('copy', '{path}')</script>"
        '<div class="box"><div class="box-head"><div class="flex-1">Recent Builds</div>'
        "<a>history</a><a>rss</a></div><table><thead><tr>"
        + "".join(f"<th>{label}</th>" for label in headers)
        + f"</tr></thead><tbody>{rows}</tbody></table></div></html>"
    )


def reply(html, status=200, count=0):
    return dict(ok=True, html_redacted=html, status=status, outside_identity_count=count)


class Clock:
    def __init__(self):
        self.now = 0
        self.sleeps = []
        self.time = SimpleNamespace(monotonic=lambda: self.now, sleep=self.advance)

    def advance(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds
