"""Base model for grouping raw sensor readings by sensor type."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Iterable, List, Tuple

from sensors.desktop_sensor_probe import SensorReading


@dataclass(frozen=True)
class BaseSensorModel:
    """Shared behavior that every concrete sensor model should inherit."""

    sensor_type: ClassVar[str] = "base"
    reading_names: ClassVar[Tuple[str, ...]] = ()
    reading_prefixes: ClassVar[Tuple[str, ...]] = ()
    default_unit: ClassVar[str] = ""

    def matches_reading(self, reading: SensorReading) -> bool:
        """Return whether a reading belongs to this sensor type."""

        if reading.name in self.reading_names:
            return True
        return any(
            reading.name.startswith(prefix)
            for prefix in self.reading_prefixes
        )

    def matching_readings(
        self,
        readings: Iterable[SensorReading],
    ) -> List[SensorReading]:
        """Return the readings that belong to this sensor type."""

        return [reading for reading in readings if self.matches_reading(reading)]

    def values(
        self,
        readings: Iterable[SensorReading],
    ) -> List[float]:
        """Return the numeric values for this sensor type."""

        return [reading.value for reading in self.matching_readings(readings)]

    def latest_value(
        self,
        readings: Iterable[SensorReading],
    ) -> float | None:
        """Return the latest value for this sensor type when one exists."""

        values = self.values(readings)
        if not values:
            return None
        return values[-1]

    def reading_to_json(self, reading: SensorReading) -> dict[str, float | str]:
        """Return one reading in a JSON-friendly shape."""

        return {
            "name": reading.name,
            "value": reading.value,
            "unit": reading.unit,
        }

    def to_json(
        self,
        readings: Iterable[SensorReading],
    ) -> dict[str, object]:
        """Return this sensor type and its readings in a JSON-friendly shape."""

        matching_readings = self.matching_readings(readings)
        return {
            "sensor_type": self.sensor_type,
            "default_unit": self.default_unit,
            "readings": [
                self.reading_to_json(reading)
                for reading in matching_readings
            ],
        }
