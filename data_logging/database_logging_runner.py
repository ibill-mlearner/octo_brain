"""Orchestrate raw sensor writes through the SQLite data logger."""

from __future__ import annotations

import platform
from pathlib import Path

from .logger import DataLogger, utc_now_iso
from .runtime_sample_collector import RuntimeSampleCollector


class DatabaseLoggingRunner:
    """Run a raw-sensor logging pass through the DataLogger."""

    def __init__(
        self,
        sample_collector: RuntimeSampleCollector | None = None,
    ):
        self.sample_collector = sample_collector or RuntimeSampleCollector()

    def run(
        self,
        db_path: Path,
        steps: int,
    ) -> dict[str, int]:
        """Write raw sensor samples through the public DataLogger path."""
        with DataLogger(db_path) as logger:
            logger.initialize()
            run_id = logger.create_run(
                label="main-database-raw-sensors",
                metadata={
                    "created_by": "main_database.py",
                    "purpose": "exercise data_logging with raw sensor inputs",
                    "python_version": platform.python_version(),
                    "platform": platform.platform(),
                    "started_at": utc_now_iso(),
                    "steps": steps,
                },
            )

            for step in range(steps):
                logger.log_raw_samples(
                    run_id,
                    step,
                    self.sample_collector.collect(step),
                )

            return {
                "runs": logger.count_rows("runs"),
                "raw_sensor_samples": logger.count_rows("raw_sensor_samples"),
            }
