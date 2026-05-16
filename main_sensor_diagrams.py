"""Generate sensor validation diagrams keyed by scanner kernel steps.

This is a thin runnable demo. The plotting/dataframe behavior lives in
``validation_diagrams.sensor_kernel_diagram`` so the core sensor and node-role
modules stay focused on runtime behavior.
"""

from __future__ import annotations

from validation_diagrams.sensor_kernel_diagram import SensorKernelDiagrammer


def main() -> None:
    """Write the initial sensor/kernel-step CSV and matplotlib diagrams."""

    diagrammer = SensorKernelDiagrammer()
    artifacts = diagrammer.build_artifacts()
    for name, path in artifacts.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
