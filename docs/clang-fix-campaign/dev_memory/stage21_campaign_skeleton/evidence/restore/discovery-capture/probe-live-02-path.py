"""Offline inspection only: parse saved HTML, then compare URL parsing and capture guard."""

import json
import subprocess
from html.parser import HTMLParser
from pathlib import Path


class Frames(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.frames: list[dict[str, object]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "iframe":
            self.frames.append({"line": self.getpos()[0], "src": dict(attrs).get("src")})


here = Path(__file__).resolve().parent
parser = Frames()
parser.feed((here / "live-02/06.response.html").read_text())
assert len(parser.frames) == 1
source = parser.frames[0]["src"]
script = """
const {exactLink,fixedError} = await import(
  './docs/clang-fix-campaign/dev_memory/stage21_campaign_skeleton/'
  + 'evidence/restore/discovery-capture/capture.mjs');
const raw = process.argv[1];
const base = 'https://quickbuild.tizen.org/build/1204736/html_report';
const url = new URL(raw, base);
let captureResult;
try { captureResult = {ok:true,url:exactLink(raw,base)}; }
catch(error) { captureResult = {ok:false,error:fixedError(error)}; }
console.log(JSON.stringify({raw,standard_url:url.href,origin:url.origin,path:url.pathname,
  query:url.search,fragment:url.hash,capture:captureResult,network_requests:0}));
"""
result = subprocess.run(
    ["/home/linhao/.local/bin/node", "--input-type=module", "-e", script, str(source)],
    cwd=here.parents[6], capture_output=True, text=True, check=True,
)
facts = json.loads(result.stdout)
facts["source"] = "live-02/06.response.html"
facts["line"] = parser.frames[0]["line"]
facts["note"] = "Computed offline, not an observed iframe response or browser request URL."
assert facts["capture"] == {"ok": False, "error": "CAPTURE_PATH_UNSUPPORTED"}
(here / "live-02/path-probe.json").write_text(json.dumps(facts, indent=2) + "\n")
print(json.dumps(facts, indent=2))
