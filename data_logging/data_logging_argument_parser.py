"""Argument parsing helpers for data-logging entrypoints."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


class DataLoggingArgumentParser:
    """Build fresh argument parsers for data-logging scripts."""

    default_description = "Write real runtime samples through the data_logging package."

    def parse_args(
        self,
        argument_definitions: Iterable[Mapping[str, Any]] | None = None,
        argv: Sequence[str] | None = None,
        description: str | None = None,
    ) -> argparse.Namespace:
        """Add the requested arguments to a new parser and parse argv."""
        parser = argparse.ArgumentParser(
            description=description or self.default_description,
        )
        for argument_definition in argument_definitions or self.database_argument_definitions():
            names = tuple(argument_definition["names"])
            options = dict(argument_definition.get("options", {}))
            parser.add_argument(*names, **options)

        return parser.parse_args(argv)

    @staticmethod
    def database_argument_definitions() -> tuple[Mapping[str, Any], ...]:
        """Return the default CLI arguments used by main_database.py."""
        default_db_path = Path("runtime_data") / "main_database.sqlite3"
        default_steps = 5

        return (
            {
                "names": ("--db-path",),
                "options": {
                    "type": Path,
                    "default": default_db_path,
                    "help": (
                        "SQLite database path to create or append to. "
                        f"Default: {default_db_path}"
                    ),
                },
            },
            {
                "names": ("--steps",),
                "options": {
                    "type": int,
                    "default": default_steps,
                    "help": f"Number of real-data logging steps to write. Default: {default_steps}",
                },
            },
        )
