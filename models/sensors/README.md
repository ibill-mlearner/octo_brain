# Sensor Models

This directory defines the data-model side of the sensor system, not the operating-system probing logic. The files here describe how raw readings are named, grouped, filtered, and serialized after a sensor implementation has already collected them. `base_sensor.py` is the shared foundation because it owns the `SensorReading` data shape and the `BaseSensorModel` grouping behavior that the concrete model files inherit. The concrete files such as `cpu_sensor.py`, `memory_sensor.py`, and `temperature_sensor.py` keep their scope intentionally small: they declare the expected reading names, reading prefixes, and default units for one family of readings. The package initializer, `__init__.py`, gathers those models into a stable public import surface and defines `DEFAULT_SENSOR_MODELS` for callers that want the standard grouping order.

## Responsibility boundary

Sensor models should stay focused on structure and classification. They should not call `psutil`, inspect the operating system, read files, poll hardware, or decide how often data is collected. That collection behavior belongs in the top-level `sensors` package, while this directory answers questions like "does this reading belong to CPU?" and "how should this grouped reading appear in JSON?" Keeping that split makes it easier to add new collection sources without rewriting the model layer.

## File guide

- `__init__.py` exports the sensor model classes, the shared `SensorReading` model, and `DEFAULT_SENSOR_MODELS` so downstream code can import the model API from one package location.
- `base_sensor.py` defines `SensorReading`, which carries the reading name, numeric value, optional unit, source, raw payload, and collection method, and it defines `BaseSensorModel`, which provides matching, filtering, value extraction, latest-value lookup, and JSON conversion helpers.
- `battery_sensor.py` defines `BatterySensorModel` for `battery_percent` and `battery_seconds_left` readings.
- `cpu_sensor.py` defines `CpuSensorModel` for `cpu_percent` readings and declares `%` as the default unit.
- `disk_sensor.py` defines `DiskSensorModel` for disk usage and disk I/O byte counters.
- `fan_sensor.py` defines `FanSensorModel` for runtime-exposed fan speed readings that use the `fan_` prefix and `rpm` as the default unit.
- `load_sensor.py` defines `LoadSensorModel` for standard-library load averages: `load_1m`, `load_5m`, and `load_15m`.
- `memory_sensor.py` defines `MemorySensorModel` for available-memory and used-memory-percent readings.
- `network_sensor.py` defines `NetworkSensorModel` for sent and received network byte counters.
- `process_sensor.py` defines `ProcessSensorModel` for process runtime readings such as `process_time`.
- `temperature_sensor.py` defines `TemperatureSensorModel` for thermal readings that use the `temperature_` prefix and `C` as the default unit.

## Adding a sensor model

When adding a new model, create a small file that inherits `BaseSensorModel` and declares only the grouping metadata needed to recognize its readings. Prefer exact `reading_names` when the collector produces a fixed name, and use `reading_prefixes` when the collector may append platform-specific labels. Add the model to `DEFAULT_SENSOR_MODELS` only when it should participate in the standard grouped JSON output. Avoid adding collection or polling code here; add that logic under `sensors/` and make it emit `SensorReading` objects that the model can recognize.
