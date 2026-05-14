"""SQLite logging utilities for spatial-memory viability testing."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class RawSample:
    source: str
    value: float
    unit: str = ""


class DataLogger:
    """Small SQLite logger for early prototype viability runs."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
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

            create table if not exists node_messages (
                message_id integer primary key autoincrement,
                run_id integer not null,
                step integer not null,
                node_id text not null,
                role text not null,
                state real not null,
                error real not null,
                confidence real not null,
                urgency real not null,
                payload_json text not null,
                captured_at text not null,
                foreign key (run_id) references runs(run_id)
            );

            create table if not exists memory_steps (
                memory_step_id integer primary key autoincrement,
                run_id integer not null,
                step integer not null,
                position_x integer not null,
                position_y integer not null,
                position_z integer not null,
                error real not null,
                reflex_triggered integer not null,
                write_back integer not null,
                payload_json text not null,
                captured_at text not null,
                foreign key (run_id) references runs(run_id)
            );
            """
        )
        self.connection.commit()

    def create_run(self, label: str = "spatial-memory-viability", metadata: Mapping[str, Any] | None = None) -> int:
        cursor = self.connection.execute(
            "insert into runs (started_at, label, metadata_json) values (?, ?, ?)",
            (utc_now_iso(), label, json.dumps(dict(metadata or {}), sort_keys=True)),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def log_raw_samples(self, run_id: int, step: int, samples: Iterable[RawSample]) -> None:
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

    def log_node_message(self, run_id: int, step: int, message: Mapping[str, Any], payload: Mapping[str, Any] | None = None) -> None:
        self.connection.execute(
            """
            insert into node_messages
                (run_id, step, node_id, role, state, error, confidence, urgency, payload_json, captured_at)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                step,
                str(message.get("node_id", "")),
                str(message.get("role", "")),
                float(message.get("state", 0.0)),
                float(message.get("error", 0.0)),
                float(message.get("confidence", 0.0)),
                float(message.get("urgency", 0.0)),
                json.dumps(dict(payload or {}), sort_keys=True),
                utc_now_iso(),
            ),
        )
        self.connection.commit()

    def log_memory_step(
        self,
        run_id: int,
        step: int,
        position: Sequence[int | float],
        error: float = 0.0,
        reflex_triggered: bool = False,
        write_back: bool = True,
        payload: Mapping[str, Any] | None = None,
    ) -> None:
        if len(position) != 3:
            raise ValueError("position must contain exactly three coordinates")

        self.connection.execute(
            """
            insert into memory_steps
                (run_id, step, position_x, position_y, position_z, error, reflex_triggered, write_back, payload_json, captured_at)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                step,
                int(position[0]),
                int(position[1]),
                int(position[2]),
                float(error),
                int(reflex_triggered),
                int(write_back),
                json.dumps(dict(payload or {}), sort_keys=True),
                utc_now_iso(),
            ),
        )
        self.connection.commit()

    def count_rows(self, table_name: str) -> int:
        allowed_tables = {"runs", "raw_sensor_samples", "node_messages", "memory_steps"}
        if table_name not in allowed_tables:
            raise ValueError(f"unsupported table: {table_name}")
        row = self.connection.execute(f"select count(*) as count from {table_name}").fetchone()
        return int(row["count"])
