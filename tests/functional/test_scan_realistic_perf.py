import time
from pathlib import Path

from gbs_analyzer.scan_and_extract import scan_buildlog


def write_densified_buildlog(path: Path) -> None:
    """Create a compact synthetic log with realistic command/event density."""

    diagnostic_index = 0
    with path.open("w", encoding="utf-8") as file:
        file.write("+ %prep\n")
        file.write("+ %build\n")
        for index in range(500):
            file.write(f"+ gcc -Iinclude -DIDX={index} -c src/file{index}.c\n")
            for noise in range(12):
                file.write(
                    "build output "
                    f"{index}:{noise} "
                    "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n"
                )
            if index % 10 == 0:
                diagnostic_index += 1
                warning = f"synthetic warning {diagnostic_index}"
                file.write(
                    f"src/file{index}.c:{index + 1}:2: warning: {warning}\n"
                )
            if index % 25 == 0:
                diagnostic_index += 1
                file.write(
                    f"src/file{index}.c:{index + 1}:4: error: synthetic error {diagnostic_index}\n"
                )
                file.write(f"make[2]: *** [src/file{index}.o] Error 1\n")

        filler = "dense filler without diagnostic marker " + ("x" * 180) + "\n"
        while path.stat().st_size < 10 * 1024 * 1024:
            file.write(filler)


def test_densified_scan_perf_under_two_seconds(tmp_path: Path) -> None:
    buildlog = tmp_path / "densified_buildlog"
    write_densified_buildlog(buildlog)

    started = time.perf_counter()
    result = scan_buildlog(buildlog)
    elapsed = time.perf_counter() - started

    assert buildlog.stat().st_size >= 10 * 1024 * 1024
    assert len(result.commands) == 500
    assert len(result.events) == 90
    assert elapsed < 2.0
