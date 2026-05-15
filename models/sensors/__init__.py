"""Sensor models grouped by the raw readings collected so far."""

from .base_sensor import BaseSensorModel
from .battery_sensor import BatterySensorModel
from .cpu_sensor import CpuSensorModel
from .disk_sensor import DiskSensorModel
from .fan_sensor import FanSensorModel
from .load_sensor import LoadSensorModel
from .memory_sensor import MemorySensorModel
from .network_sensor import NetworkSensorModel
from .process_sensor import ProcessSensorModel
from .temperature_sensor import TemperatureSensorModel

DEFAULT_SENSOR_MODELS = (
    CpuSensorModel(),
    MemorySensorModel(),
    DiskSensorModel(),
    NetworkSensorModel(),
    BatterySensorModel(),
    TemperatureSensorModel(),
    FanSensorModel(),
    LoadSensorModel(),
    ProcessSensorModel(),
)

__all__ = [
    "BaseSensorModel",
    "BatterySensorModel",
    "CpuSensorModel",
    "DEFAULT_SENSOR_MODELS",
    "DiskSensorModel",
    "FanSensorModel",
    "LoadSensorModel",
    "MemorySensorModel",
    "NetworkSensorModel",
    "ProcessSensorModel",
    "TemperatureSensorModel",
]
