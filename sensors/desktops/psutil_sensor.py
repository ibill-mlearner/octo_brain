"""psutil-backed desktop sensor collection.

This file contains the richer desktop sensor implementation that uses the optional ``psutil`` package. It is responsible for loading psutil lazily enough that the repository does not require that dependency to import the sensor package. The class gathers CPU, memory, disk, network, battery, temperature, and fan values when the runtime exposes them. Platform-specific psutil failures are treated as missing readings so one unsupported counter does not break the entire sample. The output remains a list of shared ``SensorReading`` models so downstream grouping logic can stay independent of psutil.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
from typing import Any, List

from models.sensors import SensorReading
from ..base_sensor import BaseSensor


class DesktopPsutilSensor(BaseSensor):
    """Collect desktop readings through the optional psutil package.

    The class owns psutil-specific field names, optional sensor probes, and safe handling for unsupported platform counters.
    """

    name = "desktop_psutil"
    reading_names = (
        "cpu_percent",
        "memory_available",
        "memory_used_percent",
        "disk_used_percent",
        "disk_read_bytes",
        "disk_write_bytes",
        "net_bytes_sent",
        "net_bytes_recv",
        "battery_percent",
        "battery_seconds_left",
    )
    reading_prefixes = (
        "temperature_",
        "fan_",
    )
    source = "desktop"
    collection_method = "psutil"

    def __init__(self) -> None:
        """Load and cache the optional psutil module for this sensor instance.

        Keeping the module on the instance lets long-lived sensors avoid repeating import discovery during every polling loop.
        """

        self.psutil = self._load_psutil()

    def _load_psutil(self) -> Any | None:
        """Return psutil when installed without making it mandatory.

        If psutil is not available, the sensor can still be constructed and will simply report no psutil-backed readings.
        """

        if importlib.util.find_spec("psutil") is None:
            return None
        return importlib.import_module("psutil")

    def collect_readings(self) -> List[SensorReading]:
        """Collect desktop readings when psutil is available.

        The method gathers each reading family independently so unsupported optional psutil probes can be skipped without losing all available values.
        """

        if self.psutil is None:
            return []

        readings: List[SensorReading] = []
        readings.extend(self._cpu_readings())
        readings.extend(self._memory_readings())
        readings.extend(self._disk_readings())
        readings.extend(self._network_readings())
        readings.extend(self._battery_readings())
        readings.extend(self._temperature_readings())
        readings.extend(self._fan_readings())
        return readings

    def _safe_psutil_call(
        self,
        method_name: str,
        default: Any = None,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Call a psutil method and treat unsupported platform probes as empty.

        This wrapper keeps platform-specific ``psutil`` exceptions local to collection and returns the supplied default for unavailable counters.
        """

        try:
            return getattr(self.psutil, method_name)(*args, **kwargs)
        except (FileNotFoundError, NotImplementedError, OSError):
            return default

    def _cpu_readings(self) -> List[SensorReading]:
        """Return CPU usage readings.

        The reading uses psutil's instantaneous CPU percent call and stores the raw numeric value alongside the normalized name.
        """

        value = self._safe_psutil_call("cpu_percent", 0.0, interval=0.0)
        return [self.build_reading("cpu_percent", value, "%", raw_data=value)]

    def _memory_readings(self) -> List[SensorReading]:
        """Return virtual memory readings.

        Available memory and used-memory percent are emitted from the same psutil memory payload so both readings share the raw source data.
        """

        memory = self._safe_psutil_call("virtual_memory")
        if memory is None:
            return []
        return [
            self.build_reading(
                "memory_available",
                memory.available,
                "bytes",
                raw_data=memory,
            ),
            self.build_reading(
                "memory_used_percent",
                memory.percent,
                "%",
                raw_data=memory,
            ),
        ]

    def _disk_readings(self) -> List[SensorReading]:
        """Return disk usage and I/O readings.

        Disk usage is collected for the current working directory, while byte counters are included only when the platform exposes disk I/O stats.
        """

        readings: List[SensorReading] = []
        disk_usage = self._safe_psutil_call("disk_usage", None, os.getcwd())
        if disk_usage is not None:
            readings.append(
                self.build_reading(
                    "disk_used_percent",
                    disk_usage.percent,
                    "%",
                    raw_data=disk_usage,
                )
            )

        disk_io = self._safe_psutil_call("disk_io_counters")
        if disk_io is not None:
            readings.extend(
                [
                    self.build_reading(
                        "disk_read_bytes",
                        disk_io.read_bytes,
                        "bytes",
                        raw_data=disk_io,
                    ),
                    self.build_reading(
                        "disk_write_bytes",
                        disk_io.write_bytes,
                        "bytes",
                        raw_data=disk_io,
                    ),
                ]
            )
        return readings

    def _network_readings(self) -> List[SensorReading]:
        """Return network I/O readings.

        The method emits sent and received byte counters together because they come from the same psutil network I/O payload.
        """

        network_io = self._safe_psutil_call("net_io_counters")
        if network_io is None:
            return []
        return [
            self.build_reading(
                "net_bytes_sent",
                network_io.bytes_sent,
                "bytes",
                raw_data=network_io,
            ),
            self.build_reading(
                "net_bytes_recv",
                network_io.bytes_recv,
                "bytes",
                raw_data=network_io,
            ),
        ]

    def _battery_readings(self) -> List[SensorReading]:
        """Return battery readings when the platform exposes them.

        Battery percent is always included when a battery payload exists, and seconds remaining is included only when psutil reports a known finite value.
        """

        battery = self._safe_psutil_call("sensors_battery")
        if battery is None:
            return []

        readings = [
            self.build_reading(
                "battery_percent",
                battery.percent,
                "%",
                raw_data=battery,
            )
        ]
        if battery.secsleft not in (
            self.psutil.POWER_TIME_UNLIMITED,
            self.psutil.POWER_TIME_UNKNOWN,
        ):
            readings.append(
                self.build_reading(
                    "battery_seconds_left",
                    battery.secsleft,
                    "seconds",
                    raw_data=battery,
                )
            )
        return readings

    def _temperature_readings(self) -> List[SensorReading]:
        """Return thermal readings when the platform exposes them.

        Temperature names include the psutil sensor name and entry label so multiple thermal sources can coexist without overwriting one another.
        """

        readings: List[SensorReading] = []
        temperatures = self._safe_psutil_call("sensors_temperatures", {})
        for sensor_name, entries in temperatures.items():
            for index, entry in enumerate(entries):
                if entry.current is None:
                    continue
                label = entry.label or str(index)
                readings.append(
                    self.build_reading(
                        f"temperature_{sensor_name}_{label}",
                        entry.current,
                        "C",
                        raw_data=entry,
                    )
                )
        return readings

    def _fan_readings(self) -> List[SensorReading]:
        """Return fan speed readings when the platform exposes them.

        Fan names include the psutil sensor name and entry label so grouped fan readings can retain source-specific identity.
        """

        readings: List[SensorReading] = []
        fans = self._safe_psutil_call("sensors_fans", {})
        for sensor_name, entries in fans.items():
            for index, entry in enumerate(entries):
                if entry.current is None:
                    continue
                label = entry.label or str(index)
                readings.append(
                    self.build_reading(
                        f"fan_{sensor_name}_{label}",
                        entry.current,
                        "rpm",
                        raw_data=entry,
                    )
                )
        return readings
