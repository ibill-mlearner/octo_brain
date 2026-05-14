"""Run every test in the tests/ folder from one command.

Usage:
    python run_tests.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TESTS_DIR = ROOT / "tests"
PROTO_DIR = ROOT / "spatial_memory_proto"


def main() -> int:
    if not TESTS_DIR.is_dir():
        print(f"tests folder not found: {TESTS_DIR}", file=sys.stderr)
        return 1

    # The prototype files use direct imports instead of package imports, so make
    # sure the test runner works no matter where it is launched from.
    sys.path.insert(0, str(PROTO_DIR))
    sys.path.insert(0, str(ROOT))

    suite = unittest.defaultTestLoader.discover(str(TESTS_DIR), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
