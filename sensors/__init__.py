"""Top-level package marker for sensor collection code.

This package owns the logic for gathering sensor readings and exposing sensor-related interfaces to the rest of the project. It intentionally keeps the public import path centered on ``sensors.interfaces`` so callers do not need to know where concrete implementations live. The sibling modules contain the reusable base class, desktop probe wrapper, JSON collector, and concrete desktop sensor package. Model definitions and reading grouping rules live under ``models.sensors`` instead of this package. Keeping this package thin at the root makes it easier to add new sensor families without making package initialization perform collection work.
"""
