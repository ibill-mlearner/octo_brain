"""SQLite logging utilities for raw sensor input data."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


__all__ = ["DataLogger", "RawSample", "utc_now_iso"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class RawSample:
    source: str
    value: float
    unit: str = ""


class DataLogger:
    """Small SQLite logger for raw sensor input samples."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.initialize()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "DataLogger":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def initialize(self) -> None:
        self.connection.executescript(
            """
            create table if not exists runs (
                run_id integer primary key autoincrement,
                started_at text not null,
                label text not null,
                metadata_json text not null
            );

            create table if not exists raw_sensor_samples (
                sample_id integer primary key autoincrement,
                run_id integer not null,
                step integer not null,
                source text not null,
                sample_index integer not null,
                value real not null,
                unit text not null,
                captured_at text not null,
                foreign key (run_id) references runs(run_id)
            );
            """
        )
        self.connection.commit()

    def create_run(
        self,
        label: str = "raw-sensor-inputs",
        metadata: Mapping[str, Any] | None = None,
    ) -> int:
        cursor = self.connection.execute(
            "insert into runs (started_at, label, metadata_json) values (?, ?, ?)",
            (utc_now_iso(), label, json.dumps(dict(metadata or {}), sort_keys=True)),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def log_raw_samples(
        self,
        run_id: int,
        step: int,
        samples: Iterable[RawSample],
    ) -> None:
        captured_at = utc_now_iso()
        rows = [
            (run_id, step, sample.source, index, float(sample.value), sample.unit, captured_at)
            for index, sample in enumerate(samples)
        ]
        if not rows:
            return
        self.connection.executemany(
            """
            insert into raw_sensor_samples
                (run_id, step, source, sample_index, value, unit, captured_at)
            values (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        self.connection.commit()

    def count_rows(self, table_name: str) -> int:
        allowed_tables = {"runs", "raw_sensor_samples"}
        if table_name not in allowed_tables:
            raise ValueError(f"unsupported table: {table_name}")
        row = self.connection.execute(f"select count(*) as count from {table_name}").fetchone()
        return int(row["count"])
