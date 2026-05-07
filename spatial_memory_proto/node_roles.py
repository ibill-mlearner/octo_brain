from dataclasses import dataclass
from typing import Dict, Tuple

import torch

from spatial_memory_system import SpatialMemorySystem
from prediction_head import PredictionHead
from decision_module import DecisionModule


@dataclass
class NodeConfig:
    node_id: str
    role: str
    channels: int = 8
    field_size: Tuple[int, int, int] = (100, 100, 100)
    window_size: Tuple[int, int, int] = (10, 10, 10)
    learning_rate: float = 5e-4


class BaseNode:
    def __init__(self, config: NodeConfig, core: SpatialMemorySystem):
        self.config = config
        self.core = core
        self.position = torch.zeros(3)
        self.velocity = torch.zeros(3)
        self.active_state = torch.zeros(1, config.channels, *config.window_size)

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
    def __init__(self, config: NodeConfig, core: SpatialMemorySystem):
        super().__init__(config, core)
        self.predictor = PredictionHead(config.channels)

    def sense_and_predict(self):
        patch = self.core.read_patch(self.position)
        pred = self.predictor(self.active_state, patch)
        return patch, pred


class ReflexNode(BaseNode):
    def check(self, error: float, threshold: float = 0.02):
        urgency = min(1.0, error / max(threshold, 1e-6))
        trigger = error > threshold
        return trigger, urgency


class DecisionNode(BaseNode):
    def __init__(self, config: NodeConfig, core: SpatialMemorySystem):
        super().__init__(config, core)
        self.decision = DecisionModule(config.channels)

    def decide(self, error: float):
        action = self.decision(self.active_state, torch.tensor(error), self.velocity)
        return torch.round(action)


class ActorNode(BaseNode):
    def act(self, action: torch.Tensor):
        next_position = self.core._clamp_position(self.position + action)
        feedback = float(torch.norm(next_position - self.position).item())
        self.velocity = (next_position - self.position)
        self.position = next_position
        return feedback
