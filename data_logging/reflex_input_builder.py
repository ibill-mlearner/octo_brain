"""Build reflex-shaped node messages from logged raw samples."""

from __future__ import annotations

from .logger import RawSample


class ReflexInputBuilder:
    """Shape raw samples into the message fields stored for reflex feedback."""

    def build(
        self,
        step: int,
        samples: list[RawSample],
    ) -> dict[str, float | str]:
        """Build a reflex-oriented node message from runtime samples."""
        values_by_source = {sample.source: sample.value for sample in samples}
        cpu_count = max(values_by_source.get("system.cpu_count", 1.0), 1.0)
        load_average = values_by_source.get("system.load_average.1m", 0.0)
        disk_total = max(values_by_source.get("disk.cwd.total", 1.0), 1.0)
        disk_used = values_by_source.get("disk.cwd.used", 0.0)
        process_time = values_by_source.get("process.cpu_time", 0.0)

        load_ratio = load_average / cpu_count
        disk_ratio = disk_used / disk_total
        process_time_ratio = process_time / max(float(step + 1), 1.0)
        reflex_error = load_ratio + disk_ratio + process_time_ratio

        return {
            "node_id": "reflex-raw-input-preview",
            "role": "reflex",
            "state": float(step),
            "error": reflex_error,
            "confidence": 1.0,
            "urgency": min(reflex_error, 1.0),
        }
