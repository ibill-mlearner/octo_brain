from typing import Dict

import torch

from tentacles.spatial_memory_system import SpatialMemorySystem

from .node_config import NodeConfig


class BaseNode:
    """Shared moving-window state for sensor, reflex, decision, and actor nodes."""

    def __init__(self, config: NodeConfig, core: SpatialMemorySystem):
        self.config = config
        self.core = core
        self.device = core.memory_field.device
        self.position = torch.zeros(3, device=self.device)
        self.velocity = torch.zeros(3, device=self.device)
        self.active_state = torch.zeros(1, config.channels, *config.window_size, device=self.device)

    def sync_from(self, other: "BaseNode") -> None:
        self.position = other.position.detach().to(self.device)
        self.velocity = other.velocity.detach().to(self.device)
        self.active_state = other.active_state.detach().to(self.device)

    def ingest_raw_values(self, values: torch.Tensor) -> torch.Tensor:
        """Role hook for pushing raw numeric readings into this node.

        Base nodes intentionally do nothing here. Sensor/actor-like nodes can
        override this shared method name so callers do not need role-specific
        ingestion code.
        """
        return self.active_state

    def _write_values_to_active(self, values: torch.Tensor) -> torch.Tensor:
        flat = values.detach().flatten().to(self.device, dtype=self.active_state.dtype)
        writable = self.active_state.flatten()
        count = min(flat.numel(), writable.numel())
        writable[:count] = flat[:count]
        return self.active_state

    def to_message(self, error: float = 0.0, confidence: float = 0.5, urgency: float = 0.0) -> Dict:
        return {
            "node_id": self.config.node_id,
            "role": self.config.role,
            "state": self.active_state.detach().cpu().mean().item(),
            "error": float(error),
            "confidence": float(confidence),
            "urgency": float(urgency),
        }
