"""Offline structural facts from the already-redacted live-04 report only."""

import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin


class Rows(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[dict[str, object]]] = []
        self.row: list[dict[str, object]] | None = None
        self.cell: dict[str, object] | None = None
        self.link: dict[str, object] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self.row = []
        elif tag in {"td", "th"} and self.row is not None:
            self.cell = {"text": "", "line": self.getpos()[0], "links": []}
            self.row.append(self.cell)
        elif tag == "a" and self.cell is not None:
            a = dict(attrs)
            self.link = {"text": "", "line": self.getpos()[0],
                         "href": a.get("href"), "class": a.get("class")}
            self.cell["links"].append(self.link)  # type: ignore[attr-defined]

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell["text"] = str(self.cell["text"]) + data
        if self.link is not None:
            self.link["text"] = str(self.link["text"]) + data

    def handle_endtag(self, tag: str) -> None:
        if tag == "a":
            self.link = None
        elif tag in {"td", "th"}:
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def main() -> None:
    here = Path(__file__).resolve().parent
    parser = Rows()
    parser.feed((here / "02.response.html").read_bytes().decode("utf-8"))
    rows = [r for r in parser.rows if r and str(r[0]["text"]).strip() == "zlib"]
    headers = [r for r in parser.rows if r and str(r[0]["text"]).strip() == "name"]
    assert len(rows) == len(headers) == 1
    links = [link for cell in rows[0] for link in cell["links"]]  # type: ignore[attr-defined]
    class_failed = [link for link in links if "failed" in (link["class"] or "").split()]
    primary = [link for link in links
               if link["href"] == "logfiles/standard/armv7l/zlib.txt"]
    assert len(primary) == 1
    run = json.loads((here / "run.json").read_text())
    result = {
        "source": "02.response.html", "offline_only": True,
        "header": headers[0], "zlib_rows": rows, "zlib_row_count": len(rows),
        "current_class_failed_matches": len(class_failed),
        "armv7l_href_count": len(primary),
        "resolved_url_not_requested": urljoin(run["pages"][1]["requested_url"], primary[0]["href"]),
        "observed_log_requests": sum("/zlib.txt" in r["url"] for r in run["requests"]),
    }
    (here / "report-structure.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"zlib_rows": len(rows), "class_failed_matches": len(class_failed),
                      "armv7l_href_count": len(primary), "log_requests": 0}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("CAPTURE_OFFLINE_INSPECTION_FAILED")
        raise SystemExit(4) from None
