"""Orchestrate real-data writes through the SQLite data logger."""

from __future__ import annotations

import platform
from pathlib import Path

from .logger import DataLogger, utc_now_iso
from .memory_position_deriver import MemoryPositionDeriver
from .reflex_input_builder import ReflexInputBuilder
from .runtime_sample_collector import RuntimeSampleCollector


class DatabaseLoggingRunner:
    """Run a real-data logging pass through each DataLogger write path."""

    def __init__(
        self,
        sample_collector: RuntimeSampleCollector | None = None,
        reflex_input_builder: ReflexInputBuilder | None = None,
        memory_position_deriver: MemoryPositionDeriver | None = None,
    ):
        self.sample_collector = sample_collector or RuntimeSampleCollector()
        self.reflex_input_builder = reflex_input_builder or ReflexInputBuilder()
        self.memory_position_deriver = memory_position_deriver or MemoryPositionDeriver()

    def run(
        self,
        db_path: Path,
        steps: int,
    ) -> dict[str, int]:
        """Write real data through each public DataLogger write path."""
        with DataLogger(db_path) as logger:
            logger.initialize()
            run_id = logger.create_run(
                label="main-database-real-data",
                metadata={
                    "created_by": "main_database.py",
                    "purpose": "exercise data_logging with real runtime inputs",
                    "python_version": platform.python_version(),
                    "platform": platform.platform(),
                    "started_at": utc_now_iso(),
                    "steps": steps,
                },
            )

            for step in range(steps):
                samples = self.sample_collector.collect(step)
                reflex_message = self.reflex_input_builder.build(step, samples)
                reflex_triggered = float(reflex_message["urgency"]) >= 0.75

                logger.log_raw_samples(run_id, step, samples)
                logger.log_node_message(
                    run_id,
                    step,
                    reflex_message,
                    payload={
                        "raw_sample_sources": [sample.source for sample in samples],
                        "note": "Preview of raw inputs intended for reflex-node feedback.",
                    },
                )
                logger.log_memory_step(
                    run_id,
                    step,
                    self.memory_position_deriver.derive(samples),
                    error=float(reflex_message["error"]),
                    reflex_triggered=reflex_triggered,
                    write_back=True,
                    payload={
                        "input_count": len(samples),
                        "reflex_urgency": float(reflex_message["urgency"]),
                    },
                )

            return {
                "runs": logger.count_rows("runs"),
                "raw_sensor_samples": logger.count_rows("raw_sensor_samples"),
                "node_messages": logger.count_rows("node_messages"),
                "memory_steps": logger.count_rows("memory_steps"),
            }
