"""Named shape for node-local active-state tensors."""

from __future__ import annotations

from typing import NamedTuple


class ActiveStateShape(NamedTuple):
    """Named dimensions for a node-local active-state tensor."""

    batch_size: int
    channels: int
    window_x: int
    window_y: int
    window_z: int

    def to_json(self) -> dict[str, int]:
        """Return the shape as a JSON-friendly mapping."""

        return {
            "batch_size": self.batch_size,
            "channels": self.channels,
            "window_x": self.window_x,
            "window_y": self.window_y,
            "window_z": self.window_z,
        }
