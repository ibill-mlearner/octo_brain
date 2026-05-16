"""Sensor-validation tables and plots keyed by scanner kernel steps.

This module is intentionally outside the core sensor, node-role, and spatial
memory packages. It is a lightweight validation/diagramming helper for looking
at raw sensor readings against the scanner's kernel-step order rather than wall
clock time.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sensors.interfaces import (
    Coordinate,
    DefaultSensorReader,
    ScannerConfig,
    ScannerEnvironment,
    SensorReader,
    SensorReading,
    SensorValueProjector,
    SpatialTokenizer,
)


DEFAULT_OUTPUT_DIR = Path("validation_diagrams/results")
DEFAULT_MIN_VALUE = 0.0
DEFAULT_MAX_VALUE = 255.0


@dataclass(frozen=True)
class SensorKernelDiagramConfig:
    """Configuration for one sensor/kernel-step validation diagram run."""

    scanner_config: ScannerConfig = ScannerConfig(
        field_size=(30, 20, 10),
        window_size=(10, 10, 5),
        stride=(10, 5, 5),
    )
    min_value: float = DEFAULT_MIN_VALUE
    max_value: float = DEFAULT_MAX_VALUE
    output_dir: Path = DEFAULT_OUTPUT_DIR
    serpentine: bool = True


class SensorKernelDiagrammer:
    """Build pandas tables and matplotlib plots for sensor kernel steps.

    The x-axis is always ``kernel_step``: the ordinal position of the scanner
    kernel as it walks the field. The data frame still carries scanner origins
    and cell coordinates so plots can choose whichever y component is useful for
    the validation question at hand.
    """

    def __init__(
        self,
        config: SensorKernelDiagramConfig | None = None,
        reader: SensorReader | None = None,
    ) -> None:
        self.config = config or SensorKernelDiagramConfig()
        self.reader = reader or DefaultSensorReader()
        self.projector = SensorValueProjector()
        self.tokenizer = SpatialTokenizer(
            window_size=self.config.scanner_config.window_size,
            add_eos=False,
        )

    def collect_readings(self) -> list[SensorReading]:
        """Collect one raw sensor pass without treating wall-clock time as x."""

        return self.reader.collect_readings()

    def kernel_origins(self) -> list[Coordinate]:
        """Return the scanner positions that define the kernel-step x-axis."""

        scanner = ScannerEnvironment(config=self.config.scanner_config)
        return scanner.raster_scan(serpentine=self.config.serpentine)

    def readings_to_dataframe(
        self,
        readings: Iterable[SensorReading],
    ) -> pd.DataFrame:
        """Project readings into scanner frames and return a plotting table."""

        readings = list(readings)
        values = self.projector.readings_to_spatial_values(readings)
        origins = self.kernel_origins()
        frames = self.tokenizer.raw_values_to_frames(
            values,
            origins,
            min_value=self.config.min_value,
            max_value=self.config.max_value,
        )

        rows: list[dict[str, float | int | str]] = []
        columns = [
            "kernel_step",
            "origin_x",
            "origin_y",
            "origin_z",
            "sensor_index",
            "sensor_name",
            "sensor_unit",
            "raw_value",
            "normalized_value",
            "coordinate_x",
            "coordinate_y",
            "coordinate_z",
        ]

        for kernel_step, frame in enumerate(frames):
            origin_x, origin_y, origin_z = frame.origin
            frame_offset = kernel_step * self.tokenizer.window_volume
            for local_index, value in enumerate(frame.values):
                sensor_index = frame_offset + local_index
                coordinate_x, coordinate_y, coordinate_z = frame.coordinates[local_index]
                reading = readings[sensor_index]
                rows.append(
                    {
                        "kernel_step": kernel_step,
                        "origin_x": origin_x,
                        "origin_y": origin_y,
                        "origin_z": origin_z,
                        "sensor_index": sensor_index,
                        "sensor_name": reading.name,
                        "sensor_unit": reading.unit or "",
                        "raw_value": float(values[sensor_index]),
                        "normalized_value": float(value),
                        "coordinate_x": coordinate_x,
                        "coordinate_y": coordinate_y,
                        "coordinate_z": coordinate_z,
                    }
                )

        return pd.DataFrame(rows, columns=columns)

    def collect_dataframe(self) -> pd.DataFrame:
        """Collect one sensor pass and return its kernel-step plotting table."""

        return self.readings_to_dataframe(self.collect_readings())

    def save_dataframe(
        self,
        dataframe: pd.DataFrame,
        filename: str = "sensor_kernel_steps.csv",
    ) -> Path:
        """Save the validation table as CSV under the configured output folder."""

        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.config.output_dir / filename
        dataframe.to_csv(output_path, index=False)
        return output_path

    def plot_sensor_values(
        self,
        dataframe: pd.DataFrame,
        y_column: str = "normalized_value",
        output_filename: str = "sensor_values_by_kernel_step.png",
    ) -> Path:
        """Plot a sensor y component against scanner kernel steps."""

        self._require_columns(
            dataframe,
            [
                "kernel_step",
                "sensor_name",
                y_column,
            ],
        )

        figure, axis = plt.subplots(figsize=(10, 6))
        for sensor_name, sensor_rows in dataframe.groupby("sensor_name"):
            axis.plot(
                sensor_rows["kernel_step"],
                sensor_rows[y_column],
                marker="o",
                label=str(sensor_name),
            )

        axis.set_title("Sensor readings by scanner kernel step")
        axis.set_xlabel("kernel step")
        axis.set_ylabel(y_column.replace("_", " "))
        axis.grid(True, alpha=0.3)
        axis.legend(loc="best")
        figure.tight_layout()

        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.config.output_dir / output_filename
        figure.savefig(output_path)
        plt.close(figure)
        return output_path

    def plot_kernel_path(
        self,
        origins: Sequence[Coordinate] | None = None,
        output_filename: str = "kernel_path_by_step.png",
    ) -> Path:
        """Plot scanner origin components against kernel steps."""

        origins = list(origins or self.kernel_origins())
        dataframe = pd.DataFrame(
            [
                {
                    "kernel_step": kernel_step,
                    "origin_x": origin[0],
                    "origin_y": origin[1],
                    "origin_z": origin[2],
                }
                for kernel_step, origin in enumerate(origins)
            ]
        )

        figure, axis = plt.subplots(figsize=(10, 6))
        for column in ["origin_x", "origin_y", "origin_z"]:
            axis.plot(
                dataframe["kernel_step"],
                dataframe[column],
                marker="o",
                label=column,
            )

        axis.set_title("Scanner origin by kernel step")
        axis.set_xlabel("kernel step")
        axis.set_ylabel("origin component")
        axis.grid(True, alpha=0.3)
        axis.legend(loc="best")
        figure.tight_layout()

        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.config.output_dir / output_filename
        figure.savefig(output_path)
        plt.close(figure)
        return output_path

    def build_artifacts(self) -> dict[str, Path]:
        """Collect one pass and write the starting validation CSV and plots."""

        dataframe = self.collect_dataframe()
        return {
            "sensor_table": self.save_dataframe(dataframe),
            "sensor_plot": self.plot_sensor_values(dataframe),
            "kernel_path_plot": self.plot_kernel_path(),
        }

    @staticmethod
    def _require_columns(
        dataframe: pd.DataFrame,
        columns: Sequence[str],
    ) -> None:
        missing_columns = [column for column in columns if column not in dataframe]
        if missing_columns:
            raise ValueError(
                "dataframe is missing required columns: "
                + ", ".join(missing_columns)
            )
