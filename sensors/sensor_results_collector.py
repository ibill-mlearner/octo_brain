"""Continuous JSON persistence for raw sensor readings.

This file provides the long-running collector that writes sensor samples to a readable JSON document. It sits after raw collection and model grouping, so it coordinates readers, projectors, model filters, and disk persistence. The collector records grouped readings, unmodeled readings, raw numeric values, and sample metadata for later inspection. It is intentionally a persistence utility rather than a sensor implementation, which means it accepts injected reader and projector callables. The default command-line path is useful for local exploratory runs, while tests or demos can construct the class directly with alternate dependencies.
"""

from __future__ import annotations

import argparse
import json
import platform
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, List, Tuple

from models.sensors import DEFAULT_SENSOR_MODELS, BaseSensorModel

from .desktop_sensor_probe import (
    SensorReading,
    collect_readings as default_collect_readings,
    readings_to_spatial_values,
)


DEFAULT_POLL_SECONDS = 3.0
SENSOR_RESULTS_DIR = Path("test results") / "sensor_results"
SENSOR_RESULTS_FILE = SENSOR_RESULTS_DIR / "sensor_readings.json"
UNMODELED_SENSOR_TYPE = "unmodeled"


@dataclass
class SensorResultsCollector:
    """Collect raw sensor readings and append them to per-sensor JSON files."""

    output_file: Path = SENSOR_RESULTS_FILE
    delay_seconds: float = DEFAULT_POLL_SECONDS
    reader: Callable[[], List[SensorReading]] = default_collect_readings
    projector: Callable[[Iterable[SensorReading]], List[float]] = (
        readings_to_spatial_values
    )
    sensor_models: Tuple[BaseSensorModel, ...] = DEFAULT_SENSOR_MODELS

    def __post_init__(self) -> None:
        """Normalize the output path after dataclass initialization.

        This keeps callers free to pass either ``Path`` objects or path-like values while the rest of the collector works with ``Path`` consistently.
        """

        self.output_file = Path(self.output_file)

    @classmethod
    def from_command_line(cls) -> "SensorResultsCollector":
        """Build a collector from the standard sensor CLI arguments.

        The parser only configures persistence cadence and output location because reader selection stays in the collector defaults.
        """

        parser = argparse.ArgumentParser(
            description="Continuously save raw sensor readings as per-sensor JSON."
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=DEFAULT_POLL_SECONDS,
            help="seconds between sensor samples",
        )
        parser.add_argument(
            "--output",
            type=Path,
            default=SENSOR_RESULTS_FILE,
            help=(
                "base JSON path used to derive per-sensor output files; "
                "for example sensor_readings.json becomes "
                "sensor_readings_cpu.json"
            ),
        )
        args = parser.parse_args()

        return cls(
            output_file=args.output,
            delay_seconds=args.delay,
        )

    def sensor_groups_to_json(
        self,
        readings: Iterable[SensorReading],
    ) -> List[dict[str, object]]:
        """Return readings grouped through the configured sensor models.

        Each configured model decides whether it recognizes a reading, and only non-empty groups are included in the JSON-ready result.
        """

        readings = list(readings)
        return [
            sensor_model.to_json(readings)
            for sensor_model in self.sensor_models
            if sensor_model.matching_readings(readings)
        ]

    def unmodeled_readings_to_json(
        self,
        readings: Iterable[SensorReading],
    ) -> List[dict[str, float | str]]:
        """Return readings that do not match any configured sensor model.

        This preserves unexpected or newly introduced readings so they are visible instead of being silently dropped.
        """

        readings = list(readings)
        unmodeled_readings = []
        for reading in readings:
            if not any(
                sensor_model.matches_reading(reading)
                for sensor_model in self.sensor_models
            ):
                unmodeled_readings.append(BaseSensorModel().reading_to_json(reading))
        return unmodeled_readings

    def load_results(self) -> dict[str, object]:
        """Load an existing sensor-results JSON document or start a new one.

        A new document records platform information and the configured model types before samples are appended.
        """

        safe_sensor_type = re.sub(r"[^a-zA-Z0-9_.-]+", "_", sensor_type).strip("_")
        safe_sensor_type = safe_sensor_type or UNMODELED_SENSOR_TYPE

        if self.output_file.suffix:
            return self.output_file.with_name(
                f"{self.output_file.stem}_{safe_sensor_type}{self.output_file.suffix}"
            )

        return self.output_file / f"{SENSOR_RESULTS_FILE.stem}_{safe_sensor_type}.json"

    def load_results(
        self,
        sensor_type: str,
        output_path: Path | None = None,
    ) -> dict[str, object]:
        """Load one sensor-results JSON document or start a new one."""

        output_path = output_path or self.output_path_for_sensor(sensor_type)
        if not output_path.exists():
            return {
                "platform": platform.platform(),
                "sensor_type": sensor_type,
                "samples": [],
            }

        return json.loads(output_path.read_text(encoding="utf-8"))

    def save_results(self, results: dict[str, object]) -> None:
        """Persist the complete sensor-results document as readable JSON.

        The method creates the output directory on demand so command-line runs can start from a clean workspace.
        """

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(results, indent=2),
            encoding="utf-8",
        )

    def append_sample(self) -> int:
        """Collect one sensor sample, append it to disk, and return its index.

        This is the unit of work used by the continuous loop, combining reading, grouping, projection, validation, and saving.
        """

        readings = self.reader()
        sensor_groups = self.sensor_groups_to_json(readings)
        unmodeled_readings = self.unmodeled_readings_to_json(readings)
        results = self.load_results()
        samples = results.setdefault("samples", [])
        if not isinstance(samples, list):
            raise ValueError(
                "sensor results file has a non-list samples field: "
                f"{output_path}"
            )

        sample_index = len(samples)
        samples.append(
            {
                "sample_index": sample_index,
                "collected_at_utc": collected_at_utc,
                "readings": readings_json,
                "raw_values": [
                    float(reading["value"])
                    for reading in readings_json
                ],
            }
        )
        self.save_results(results, output_path)
        return sample_index

    def append_sample(self) -> dict[str, int]:
        """Collect one sample and append each sensor type to its own file."""

        readings = self.reader()
        collected_at_utc = datetime.now(timezone.utc).isoformat()
        sample_indexes = {}

        for sensor_group in self.sensor_groups_to_json(readings):
            sensor_type = str(sensor_group["sensor_type"])
            group_readings = sensor_group["readings"]
            if not isinstance(group_readings, list):
                raise ValueError(f"sensor group has non-list readings: {sensor_type}")
            sample_indexes[sensor_type] = self.append_sensor_sample(
                sensor_type,
                group_readings,
                collected_at_utc,
            )

        unmodeled_readings = self.unmodeled_readings_to_json(readings)
        if unmodeled_readings:
            sample_indexes[UNMODELED_SENSOR_TYPE] = self.append_sensor_sample(
                UNMODELED_SENSOR_TYPE,
                unmodeled_readings,
                collected_at_utc,
            )

        return sample_indexes

    def run_forever(self) -> None:
        """Continuously append samples at the configured interval.

        The loop intentionally delegates the actual sample work to ``append_sample`` so one-shot and continuous collection paths share behavior.
        """

        print(f"collecting sensor readings every {self.delay_seconds} seconds")
        print(f"writing sensor results beside {self.output_file}")

        while True:
            sample_indexes = self.append_sample()
            if sample_indexes:
                summary = ", ".join(
                    f"{sensor_type}={sample_index}"
                    for sensor_type, sample_index in sorted(sample_indexes.items())
                )
                print(f"saved sensor samples: {summary}")
            else:
                print("no sensor readings collected")
            time.sleep(self.delay_seconds)
