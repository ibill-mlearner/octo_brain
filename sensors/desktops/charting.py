"""Live charting support for desktop sensor readings.

This module keeps desktop visualization separate from collection. The chart class
owns a small pandas-backed history table, uses a stationed desktop sensor to
collect readings, and asks matplotlib to redraw the selected value streams until
its caller stops the process. It is intentionally shaped as an importable object
rather than a runnable script so another Python file can decide when to start,
stop, or embed the chart loop.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from time import sleep
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from models.sensors import SensorReading

from .desktop_sensor_station import (
    DesktopSensorStation,
    get_default_desktop_sensor_station,
)


@dataclass
class DesktopSensorLiveChart:
    """Build and refresh a matplotlib chart from desktop sensor readings.

    The class is meant to be created and driven by another Python file. A caller
    can use :meth:`run_until_interrupted` for a blocking live loop, or call
    :meth:`sample_once` and :meth:`draw` from its own event loop.
    """

    station: DesktopSensorStation | None = None
    reading_names: Sequence[str] | None = None
    max_points: int = 120
    sample_interval_seconds: float = 1.0
    title: str = "Desktop sensor readings"
    collector: Callable[[], Iterable[SensorReading]] | None = None
    figure_size: tuple[float, float] = (12.0, 7.0)
    _history: pd.DataFrame = field(
        default_factory=lambda: pd.DataFrame(
            columns=[
                "timestamp",
                "name",
                "value",
                "unit",
                "source",
                "collection_method",
            ]
        ),
        init=False,
        repr=False,
    )
    _figure: Any | None = field(default=None, init=False, repr=False)
    _axis: Any | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        """Fill in the default stationed collector after dataclass setup."""

        if self.station is None:
            self.station = get_default_desktop_sensor_station()
        if self.collector is None:
            self.collector = self.station.collect_readings

    @property
    def history(self) -> pd.DataFrame:
        """Return a defensive copy of the long-form readings history."""

        return self._history.copy()

    def sample_once(self) -> pd.DataFrame:
        """Collect one reading batch and append it to the chart history.

        The returned frame is the full long-form history after the new sample is
        appended. Rows are bounded by ``max_points`` per reading name so the live
        chart does not grow forever while the process is running.
        """

        if self.collector is None:
            return self.history

        timestamp = pd.Timestamp.now()
        rows = [
            self._reading_to_row(
                timestamp=timestamp,
                reading=reading,
            )
            for reading in self.collector()
            if self._should_track_reading(reading)
        ]
        if not rows:
            return self.history

        latest = pd.DataFrame(rows)
        self._history = pd.concat(
            [
                self._history,
                latest,
            ],
            ignore_index=True,
        )
        self._trim_history()
        return self.history

    def draw(self) -> None:
        """Redraw the matplotlib figure using the current pandas history."""

        if self._history.empty:
            return

        figure, axis = self._ensure_matplotlib_objects()
        axis.clear()

        wide_history = self._history.pivot_table(
            index="timestamp",
            columns="name",
            values="value",
            aggfunc="last",
        ).sort_index()

        for name in wide_history.columns:
            axis.plot(
                wide_history.index,
                wide_history[name],
                marker="o",
                linewidth=1.5,
                markersize=3,
                label=name,
            )

        axis.set_title(self.title)
        axis.set_xlabel("Time")
        axis.set_ylabel("Raw sensor value")
        axis.grid(True, alpha=0.3)
        axis.legend(
            loc="upper left",
            bbox_to_anchor=(1.02, 1.0),
            borderaxespad=0.0,
        )
        figure.autofmt_xdate()
        figure.tight_layout()
        figure.canvas.draw_idle()
        plt.pause(0.001)

    def update_once(self) -> pd.DataFrame:
        """Collect one sample, redraw the figure, and return the history."""

        history = self.sample_once()
        self.draw()
        return history

    def run_until_interrupted(self) -> None:
        """Keep sampling and drawing until the caller kills or interrupts it.

        ``KeyboardInterrupt`` is intentionally swallowed so callers can stop the
        loop with Ctrl+C without receiving a traceback from this chart helper.
        """

        plt.ion()
        try:
            while True:
                self.update_once()
                sleep(self.sample_interval_seconds)
        except KeyboardInterrupt:
            self.close()

    def close(self) -> None:
        """Close the chart figure owned by this object, if it exists."""

        if self._figure is not None:
            plt.close(self._figure)
            self._figure = None
            self._axis = None

    def _reading_to_row(
        self,
        timestamp: pd.Timestamp,
        reading: SensorReading,
    ) -> dict[str, Any]:
        """Convert a reading object into a pandas-friendly row."""

        return {
            "timestamp": timestamp,
            "name": reading.name,
            "value": reading.value,
            "unit": reading.unit,
            "source": reading.source,
            "collection_method": reading.collection_method,
        }

    def _should_track_reading(
        self,
        reading: SensorReading,
    ) -> bool:
        """Return whether a reading should be included in the chart."""

        if self.reading_names is None:
            return True
        return reading.name in self.reading_names

    def _trim_history(self) -> None:
        """Keep the most recent ``max_points`` rows for each reading name."""

        if self.max_points <= 0:
            return
        self._history = (
            self._history.sort_values("timestamp")
            .groupby("name", group_keys=False)
            .tail(self.max_points)
            .reset_index(drop=True)
        )

    def _ensure_matplotlib_objects(self) -> tuple[Any, Any]:
        """Create the matplotlib figure and axis lazily."""

        if self._figure is None or self._axis is None:
            self._figure, self._axis = plt.subplots(figsize=self.figure_size)
        return self._figure, self._axis
