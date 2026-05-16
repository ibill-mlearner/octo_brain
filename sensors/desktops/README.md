# Desktop Sensors

This package contains the desktop-specific collection logic for raw sensor readings. The files here are classes and helpers that know how to gather data from a desktop runtime, while the model shape for those readings lives in `models/sensors`. `psutil_sensor.py` owns the optional `psutil` collection path, `fallback_sensor.py` owns the portable standard-library fallback path, and `windows_sensor.py` keeps the Windows-only gate isolated from the generic desktop code. `desktop_sensor.py` combines the psutil and fallback paths without changing the raw readings, `desktop_sensor_station.py` keeps long-lived sensor objects stationed in memory so polling loops can call methods instead of repeatedly building new sensor objects, and `charting.py` turns stationed readings into a pandas history table and live matplotlib chart for caller-owned loops. The package initializer, `__init__.py`, should remain a thin export surface so callers can import the desktop API from `sensors.desktops` without burying orchestration logic in the initializer.

## Responsibility boundary

Desktop sensor classes should gather raw values and return `SensorReading` objects. They should not normalize values for spatial memory, mutate model definitions, or decide how grouped JSON should be shaped. The collected readings can later be grouped by `models/sensors` or projected into downstream spatial placement by other modules. This package is also the compatibility layer for older helper-style calls like `collect_readings()`, but those helpers route through the stationed sensor object rather than constructing fresh collector objects every loop.

## File guide

- `__init__.py` exports the desktop sensor classes, the station class, the station accessor, and helper functions such as `collect_readings`, `psutil_readings`, `fallback_readings`, `windows_readings`, and `readings_to_spatial_values`.
- `charting.py` defines `DesktopSensorLiveChart`, an importable object that samples the stationed desktop sensor, stores readings in pandas, and refreshes a matplotlib line chart until the caller stops it.
- `desktop_sensor.py` defines `DesktopSensor`, the default selector that calls a psutil-backed sensor first and falls back to the standard-library sensor if psutil produces no readings.
- `desktop_sensor_station.py` defines `DesktopSensorStation`, which owns persistent desktop sensor instances, exposes method-based collection, and provides the lazy process-local station used by compatibility helper functions.
- `fallback_sensor.py` defines `DesktopFallbackSensor`, which gathers portable readings from the Python standard library, including load averages where available and process time.
- `psutil_sensor.py` defines `DesktopPsutilSensor`, which loads optional `psutil` once, gathers CPU, memory, disk, network, battery, temperature, and fan readings when the platform exposes them, and treats unsupported platform probes as empty readings rather than hard failures.
- `windows_sensor.py` defines `WindowsDesktopSensor`, a Windows-gated subclass of the psutil desktop sensor that returns an empty list outside Windows runtimes.

## Usage notes

Prefer holding a `DesktopSensorStation` or a concrete sensor instance when writing a polling loop. If a caller still uses helper functions such as `collect_readings()`, those helpers reuse the lazy default station instead of recreating the full desktop sensor graph for every sample. Use `DesktopPsutilSensor` directly when you specifically want optional psutil-backed values, `DesktopFallbackSensor` when you want the portable standard-library path, and `DesktopSensor` when you want the default psutil-then-fallback behavior. Keep new desktop collection strategies in their own class files and export them through `__init__.py` only after the API is ready for broader use. For live visualization, create `DesktopSensorLiveChart` from another Python file and call `run_until_interrupted()` for a blocking chart loop, or call `update_once()` from an application-owned loop.
