"""Derive memory-step positions from logged raw samples."""

from __future__ import annotations

from .logger import RawSample


class MemoryPositionDeriver:
    """Derive simple xyz memory positions from real runtime values."""

    def derive(self, samples: list[RawSample]) -> tuple[int, int, int]:
        """Derive a storage position from runtime sample values."""
        values_by_source = {sample.source: sample.value for sample in samples}
        disk_total = max(values_by_source.get("disk.cwd.total", 1.0), 1.0)
        disk_used = values_by_source.get("disk.cwd.used", 0.0)
        disk_free = values_by_source.get("disk.cwd.free", 0.0)
        process_time = values_by_source.get("process.cpu_time", 0.0)

        return (
            int(process_time * 1000) % 100,
            int((disk_used / disk_total) * 100),
            int((disk_free / disk_total) * 100),
        )
