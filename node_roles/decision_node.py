import torch

from tentacles.decision_module import DecisionModule
from tentacles.spatial_memory_system import SpatialMemorySystem

from .base_node import BaseNode
from .node_config import NodeConfig


class DecisionNode(BaseNode):
    """Coordinates sensor/actor feedback into actions for actor nodes."""

    def __init__(self, config: NodeConfig, core: SpatialMemorySystem):
        super().__init__(config, core)
        self.decision = DecisionModule(config.channels).to(self.device)

    def decide(self, error: float):
        action = self.decision(self.active_state, torch.tensor(error, device=self.device), self.velocity)
        return torch.round(action)
