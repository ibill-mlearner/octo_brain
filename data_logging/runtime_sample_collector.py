"""Runtime sample collection for real data-logging runs."""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

from .logger import RawSample


class RuntimeSampleCollector:
    """Collect live runtime values as raw logger samples."""

    def collect(self, step: int) -> list[RawSample]:
        """Collect live machine/runtime values without other project modules."""
        disk_usage = shutil.disk_usage(Path.cwd())
        perf_counter = time.perf_counter()
        process_time = time.process_time()

        samples = [
            RawSample("process.perf_counter", perf_counter, "seconds"),
            RawSample("process.cpu_time", process_time, "seconds"),
            RawSample("system.cpu_count", float(os.cpu_count() or 0), "cores"),
            RawSample("disk.cwd.total", float(disk_usage.total), "bytes"),
            RawSample("disk.cwd.used", float(disk_usage.used), "bytes"),
            RawSample("disk.cwd.free", float(disk_usage.free), "bytes"),
            RawSample("database.step", float(step), "index"),
        ]

        if hasattr(os, "getloadavg"):
            load_1m, load_5m, load_15m = os.getloadavg()
            samples.extend(
                [
                    RawSample("system.load_average.1m", load_1m, "load"),
                    RawSample("system.load_average.5m", load_5m, "load"),
                    RawSample("system.load_average.15m", load_15m, "load"),
                ]
            )

        return samples
