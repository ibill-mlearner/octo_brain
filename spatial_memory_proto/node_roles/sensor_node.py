import torch

from prediction_head import PredictionHead
from spatial_memory_system import SpatialMemorySystem

from .base_node import BaseNode
from .node_config import NodeConfig


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
