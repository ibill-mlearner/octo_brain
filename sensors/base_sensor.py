"""Base contract for concrete sensor-gathering logic.

This file defines the small interface that runtime sensor classes should share. It does not know how to collect CPU, memory, desktop, or hardware-specific values on its own. Instead, it gives concrete sensors a consistent way to declare names, units, sources, and collection methods. The helper methods here build ``SensorReading`` objects from the model layer so gathering code and grouping code agree on the same data shape. Keeping this base class in ``sensors`` reinforces that models define structure while sensor classes define collection behavior.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Iterable, List, Tuple

from models.sensors import SensorReading


class BaseSensor(ABC):
    """Shared contract for classes that gather raw sensor readings.

    Sensor models define the reading data shape and grouping metadata. Concrete
    sensor classes define the logic for obtaining those readings from a source.
    """

    name: ClassVar[str] = "base"
    reading_names: ClassVar[Tuple[str, ...]] = ()
    reading_prefixes: ClassVar[Tuple[str, ...]] = ()
    default_unit: ClassVar[str] = ""
    source: ClassVar[str] = ""
    collection_method: ClassVar[str] = ""

    @abstractmethod
    def collect_readings(self) -> List[SensorReading]:
        """Return the current raw readings for this sensor.

        Concrete subclasses implement this method because each source has its own collection mechanism and availability rules.
        """

    def build_reading(
        self,
        name: str,
        value: float,
        unit: str | None = None,
        raw_data: Any | None = None,
        collection_method: str | None = None,
    ) -> SensorReading:
        """Build a ``SensorReading`` with this sensor's tracking metadata.

        The helper centralizes source, unit, raw payload, and collection-method assignment so concrete sensors do not repeat the same dataclass construction details.
        """

        return SensorReading(
            name=name,
            value=float(value),
            unit=self.default_unit if unit is None else unit,
            source=self.source or self.name,
            raw_data=raw_data,
            collection_method=collection_method or self.collection_method,
        )

    def readings_to_spatial_values(
        self,
        readings: Iterable[SensorReading],
    ) -> List[float]:
        """Return numeric values in collection order for downstream placement.

        This deliberately strips labels and units only after collection so later spatial placement code can consume a plain value stream without owning sensor metadata logic.
        """

        return [reading.value for reading in readings]
