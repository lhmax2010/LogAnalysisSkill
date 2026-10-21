"""Append-only redacted page evidence shared by reading and discovery."""

from pathlib import Path

from ci_triage.qb_redact import EvidenceRedactionError, PageRedactor


def archive(root: Path, request_id: str, path: str, html: str) -> str:
    redactor = PageRedactor()
    data = html.encode("utf-8")
    redactor.check_bytes(data)
    directory = root / "qb_evidence" / request_id
    directory.mkdir(parents=True, exist_ok=True)
    numbers = [
        int(p.name.split(".", 1)[0])
        for p in directory.glob("*.html")
        if p.name.split(".", 1)[0].isdigit()
    ]
    name = (
        f"{max(numbers, default=0) + 1:02d}."
        + path.removeprefix("/build/").lstrip("/").replace("/", "-")
        + ".html"
    )
    output = directory / name
    try:
        output.write_bytes(data)
        redactor.check_bytes(output.read_bytes())
    except (OSError, EvidenceRedactionError):
        output.unlink(missing_ok=True)
        raise
    return str(output.relative_to(root))
