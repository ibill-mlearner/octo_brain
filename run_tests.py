"""Run every test in the tests/ folder from one command.

Usage:
    python run_tests.py

The runner prints results to the console and also writes the same output to a
timestamped text file in the "test results" folder.
"""

from __future__ import annotations

import inspect
import io
import sys
import unittest
from datetime import datetime
from pathlib import Path
from typing import TextIO


ROOT = Path(__file__).resolve().parent
TESTS_DIR = ROOT / "tests"
RESULTS_DIR = ROOT / "test results"


def expectation_lines_for(test: unittest.TestCase) -> list[str]:
    """Return speculative expectation comments attached to one test method."""
    method_name = getattr(test, "_testMethodName", "")
    method = getattr(test, method_name, None)
    if method is None:
        return ["This is what I expect to happen, the test should complete without failure or error."]

    try:
        source = inspect.getsource(method)
    except (OSError, TypeError):
        return ["This is what I expect to happen, the test should complete without failure or error."]

    expectations = []
    current_expectation: list[str] = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("# This is what I expect to happen,"):
            if current_expectation:
                expectations.append(" ".join(current_expectation))
            current_expectation = [stripped.removeprefix("# ")]
            continue

        if current_expectation and stripped.startswith("# "):
            current_expectation.append(stripped.removeprefix("# "))
            continue

        if current_expectation:
            expectations.append(" ".join(current_expectation))
            current_expectation = []

    if current_expectation:
        expectations.append(" ".join(current_expectation))

    if expectations:
        return expectations
    return ["This is what I expect to happen, the test should complete without failure or error."]


class ExpectationTextTestResult(unittest.TextTestResult):
    """Text result that pairs expected outcomes with actual test outcomes."""

    def startTest(self, test: unittest.TestCase) -> None:
        unittest.TestResult.startTest(self, test)
        if not self.showAll:
            return

        self.stream.writeln(self.getDescription(test))
        for expectation in expectation_lines_for(test):
            self.stream.writeln(expectation)
        self.stream.flush()

    def addSuccess(self, test: unittest.TestCase) -> None:
        unittest.TestResult.addSuccess(self, test)
        if self.showAll:
            self._write_actual_result(
                actual="the test completed without failure or error",
                result="OK",
            )
        elif self.dots:
            self.stream.write(".")
            self.stream.flush()

    def addError(self, test: unittest.TestCase, err) -> None:
        unittest.TestResult.addError(self, test, err)
        if self.showAll:
            self._write_actual_result(
                actual="the test raised an unexpected error",
                result="ERROR",
            )
        elif self.dots:
            self.stream.write("E")
            self.stream.flush()

    def addFailure(self, test: unittest.TestCase, err) -> None:
        unittest.TestResult.addFailure(self, test, err)
        if self.showAll:
            self._write_actual_result(
                actual="an assertion did not match the expected outcome",
                result="FAIL",
            )
        elif self.dots:
            self.stream.write("F")
            self.stream.flush()

    def addSkip(self, test: unittest.TestCase, reason: str) -> None:
        unittest.TestResult.addSkip(self, test, reason)
        if self.showAll:
            self._write_actual_result(
                actual=f"the test was skipped because {reason}",
                result="SKIP",
            )
        elif self.dots:
            self.stream.write("s")
            self.stream.flush()

    def addExpectedFailure(self, test: unittest.TestCase, err) -> None:
        unittest.TestResult.addExpectedFailure(self, test, err)
        if self.showAll:
            self._write_actual_result(
                actual="the test failed in the expected way",
                result="EXPECTED FAILURE",
            )
        elif self.dots:
            self.stream.write("x")
            self.stream.flush()

    def addUnexpectedSuccess(self, test: unittest.TestCase) -> None:
        unittest.TestResult.addUnexpectedSuccess(self, test)
        if self.showAll:
            self._write_actual_result(
                actual="the test passed even though a failure was expected",
                result="UNEXPECTED SUCCESS",
            )
        elif self.dots:
            self.stream.write("u")
            self.stream.flush()

    def _write_actual_result(
        self,
        actual: str,
        result: str,
    ) -> None:
        self.stream.writeln(f"What actually happened, {actual}.")
        self.stream.writeln(f"This is what the test result was, {result}.")
        self.stream.writeln()
        self.stream.flush()


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

    # The top-level modules use direct imports, so make sure the test runner
    # works no matter where it is launched from.
    sys.path.insert(0, str(ROOT))

    # Anchor discovery at the repository root so nested test packages are
    # imported as ``tests.<package>`` instead of colliding with root packages
    # such as ``sensors``.
    suite = unittest.defaultTestLoader.discover(
        str(TESTS_DIR), pattern="test_*.py", top_level_dir=str(ROOT)
    )
    output = io.StringIO()
    result = unittest.TextTestRunner(
        stream=output,
        verbosity=2,
        resultclass=ExpectationTextTestResult,
    ).run(suite)
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
