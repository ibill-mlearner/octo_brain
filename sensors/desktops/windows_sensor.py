"""Windows-specific desktop sensor collection.

This file isolates the Windows-only desktop sensor entry point from the generic desktop selector. The implementation subclasses the psutil-backed sensor because Windows support still flows through the same optional psutil package. Its only extra behavior is a platform guard that returns no readings on non-Windows systems. That guard lets callers ask for Windows readings safely from any runtime without wrapping the call themselves. Keeping this class small makes it clear that Windows behavior is a constrained variant of the psutil collection path rather than a separate sensor model.
"""

from __future__ import annotations

import platform
from typing import List

from models.sensors import SensorReading

from .psutil_sensor import DesktopPsutilSensor


class WindowsDesktopSensor(DesktopPsutilSensor):
    """Collect desktop readings on Windows through psutil.

    The class inherits all psutil collection details and adds only the operating-system gate.
    """

    name = "windows_desktop"
    collection_method = "windows_psutil"

    def collect_readings(self) -> List[SensorReading]:
        """Return Windows readings only on Windows runtimes.

        Non-Windows runtimes receive an empty list so callers can keep one safe code path across platforms.
        """

        if platform.system().lower() != "windows":
            return []
        return super().collect_readings()
