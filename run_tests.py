"""Run every test in the tests/ folder from one command.

Usage:
    python run_tests.py

The runner prints results to the console and also writes the same output to a
timestamped text file in the "test results" folder.
"""

from __future__ import annotations

import io
import sys
import unittest
from datetime import datetime
from pathlib import Path
from typing import TextIO


ROOT = Path(__file__).resolve().parent
TESTS_DIR = ROOT / "tests"
PROTO_DIR = ROOT / "spatial_memory_proto"
RESULTS_DIR = ROOT / "test results"


class TeeStream:
    """Write unittest output to the console and a text file at the same time."""

    def __init__(self, *streams: TextIO):
        self.streams = streams

    def write(self, text: str) -> int:
        for stream in self.streams:
            stream.write(text)
        return len(text)

    def flush(self) -> None:
        for stream in self.streams:
            stream.flush()


def timestamped_result_path() -> Path:
    now = datetime.now()
    # Includes date, day name, hour, minute, second, and 4 fractional-second digits.
    timestamp = now.strftime("%Y-%m-%d_%A_%H-%M-%S") + f"_{now.microsecond // 100:04d}"
    return RESULTS_DIR / f"test_results_{timestamp}.txt"


def result_header(result: unittest.TestResult) -> str:
    issue_count = len(result.failures) + len(result.errors)
    skipped_count = len(result.skipped)
    if issue_count > 0:
        return (
            "TEST RUN DID NOT PASS\n"
            f"Failures: {len(result.failures)} | Errors: {len(result.errors)} | "
            f"Skipped: {skipped_count} | Tests run: {result.testsRun}\n"
            "Check the detailed output below before trusting this run.\n"
        )
    return (
        "TEST RUN PASSED\n"
        f"Failures: 0 | Errors: 0 | Skipped: {skipped_count} | Tests run: {result.testsRun}\n"
    )


def main() -> int:
    if not TESTS_DIR.is_dir():
        print(f"tests folder not found: {TESTS_DIR}", file=sys.stderr)
        return 1

    RESULTS_DIR.mkdir(exist_ok=True)
    result_path = timestamped_result_path()

    # The prototype files use direct imports instead of package imports, so make
    # sure the test runner works no matter where it is launched from.
    sys.path.insert(0, str(PROTO_DIR))
    sys.path.insert(0, str(ROOT))

    suite = unittest.defaultTestLoader.discover(str(TESTS_DIR), pattern="test_*.py")
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    saved_message = f"Saved test results to: {result_path}"
    report_text = (
        f"Saving test results to: {result_path}\n\n"
        f"{result_header(result)}\n"
        f"{output.getvalue()}\n"
        f"{saved_message}\n"
    )

    with result_path.open("w", encoding="utf-8") as result_file:
        tee = TeeStream(sys.stderr, result_file)
        print(report_text, end="", file=tee)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
