import importlib.util
import sys
import unittest
from pathlib import Path


torch_spec = importlib.util.find_spec("torch")
if torch_spec is None:
    torch = None
else:
    import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "spatial_memory_proto"))


@unittest.skipIf(torch is None, "torch is not installed")
class NodeRolesTest(unittest.TestCase):
    def test_sensor_ingest_raw_values_updates_active_state(self):
        from node_roles import NodeConfig, SensorNode
        from spatial_memory_system import SpatialMemorySystem

        core = SpatialMemorySystem(channels=1, field_size=(6, 6, 6), window_size=(3, 3, 3), movement_mode="static")
        sensor = SensorNode(NodeConfig(node_id="sensor-test", role="sensor", channels=1, window_size=(3, 3, 3)), core)

        sensor.ingest_raw_values(torch.tensor([0.25, 0.5, 0.75]))

        self.assertTrue(torch.equal(sensor.active_state.flatten()[:3], torch.tensor([0.25, 0.5, 0.75])))

    def test_actor_ingest_raw_values_keeps_only_extreme_values(self):
        from node_roles import ActorNode, NodeConfig
        from spatial_memory_system import SpatialMemorySystem

        core = SpatialMemorySystem(channels=1, field_size=(6, 6, 6), window_size=(3, 3, 3), movement_mode="static")
        actor = ActorNode(NodeConfig(node_id="actor-test", role="actor", channels=1, window_size=(3, 3, 3)), core)

        actor.ingest_raw_values(torch.tensor([0.1, 0.9, -0.95, 0.2]))

        self.assertTrue(torch.equal(actor.active_state.flatten()[:2], torch.tensor([0.9, -0.95])))


if __name__ == "__main__":
    unittest.main()
