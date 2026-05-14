import torch

from spatial_memory_system import SpatialMemorySystem

from .actions import Actions
from .base_node import BaseNode
from .node_config import NodeConfig


class ActorNode(BaseNode):
    """Executes actions and reports coarse/extreme feedback signals."""

    def __init__(self, config: NodeConfig, core: SpatialMemorySystem, actions: Actions | None = None):
        super().__init__(config, core)
        self.actions = actions or Actions(core)

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
        result = self.actions.execute(self.position, action)
        self.velocity = result.velocity
        self.position = result.position
        return result.feedback
