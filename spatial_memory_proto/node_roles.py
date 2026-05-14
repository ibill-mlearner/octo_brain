from dataclasses import dataclass
from typing import Dict, Tuple

import torch

from spatial_memory_system import SpatialMemorySystem
from prediction_head import PredictionHead
from decision_module import DecisionModule


@dataclass
class NodeConfig:
    """Configuration for a local node container inside spatial memory."""
    node_id: str
    role: str
    channels: int = 8
    field_size: Tuple[int, int, int] = (100, 100, 100)
    window_size: Tuple[int, int, int] = (10, 10, 10)
    learning_rate: float = 5e-4


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


class SensorNode(BaseNode):
    """Reads raw numeric streams and local memory context without semantic parsing."""
    def __init__(self, config: NodeConfig, core: SpatialMemorySystem):
        super().__init__(config, core)
        self.predictor = PredictionHead(config.channels).to(self.device)

    def ingest_raw_values(self, values: torch.Tensor) -> torch.Tensor:
        return self._write_values_to_active(values)

    def sense_and_predict(self):
        patch = self.core.read_patch(self.position)
        pred = self.predictor(self.active_state, patch)
        return patch, pred


class ReflexNode(BaseNode):
    """Immediate urgency path for danger, high error, or slow decisions."""
    def check(self, error: float, threshold: float = 0.02):
        urgency = min(1.0, error / max(threshold, 1e-6))
        trigger = error > threshold
        return trigger, urgency


class DecisionNode(BaseNode):
    """Coordinates sensor/actor feedback into actions for actor nodes."""
    def __init__(self, config: NodeConfig, core: SpatialMemorySystem):
        super().__init__(config, core)
        self.decision = DecisionModule(config.channels).to(self.device)

    def decide(self, error: float):
        action = self.decision(self.active_state, torch.tensor(error, device=self.device), self.velocity)
        return torch.round(action)


class ActorNode(BaseNode):
    """Executes actions and reports coarse/extreme feedback signals."""
    def ingest_raw_values(self, values: torch.Tensor) -> torch.Tensor:
        super().ingest_raw_values(values)
        flat = values.detach().flatten().to(self.device, dtype=self.active_state.dtype)
        if flat.numel() == 0:
            return self.active_state

        extreme_mask = flat.abs() >= 0.8
        if not bool(extreme_mask.any().detach().cpu().item()):
            return self.active_state
        return self._write_values_to_active(flat[extreme_mask])

    def act(self, action: torch.Tensor):
        next_position = self.core._clamp_position(self.position + action)
        feedback = float(torch.norm(next_position - self.position).item())
        self.velocity = (next_position - self.position)
        self.position = next_position
        return feedback
