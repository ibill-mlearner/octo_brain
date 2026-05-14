import sys
import unittest
from pathlib import Path

try:
    import torch
except ModuleNotFoundError:  # pragma: no cover - depends on local environment
    torch = None

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@unittest.skipIf(torch is None, "torch is not installed")
class NodeRolesPackageTest(unittest.TestCase):
    def test_server_connects_role_from_single_input_with_specific_overrides(self):
        from node_roles import ActorNode, NodeRoleServer
        from tentacles.spatial_memory_system import SpatialMemorySystem

        core = SpatialMemorySystem(channels=2, field_size=(20, 20, 20), window_size=(2, 2, 2))
        server = NodeRoleServer(core)

        node = server.connect("actor", node_id="arm-actor", channels=2, window_size=(2, 2, 2))

        self.assertIsInstance(node, ActorNode)
        self.assertIs(server.get("arm-actor"), node)
        self.assertEqual(node.config.role, "actor")
        self.assertEqual(node.active_state.shape, (1, 2, 2, 2, 2))

    def test_server_connects_mapping_request(self):
        from node_roles import NodeRoleServer, SensorNode
        from tentacles.spatial_memory_system import SpatialMemorySystem

        core = SpatialMemorySystem(channels=1, field_size=(20, 20, 20), window_size=(2, 2, 2))
        server = NodeRoleServer(core)

        node = server.connect({"role": "sensor", "node_id": "camera", "channels": 1, "window_size": (2, 2, 2)})

        self.assertIsInstance(node, SensorNode)
        self.assertEqual(node.config.node_id, "camera")

    def test_actor_delegates_movement_to_actions_class(self):
        from node_roles import Actions, ActorNode, NodeConfig
        from tentacles.spatial_memory_system import SpatialMemorySystem

        core = SpatialMemorySystem(channels=1, field_size=(20, 20, 20), window_size=(2, 2, 2))
        actor = ActorNode(NodeConfig(node_id="actor", role="actor", channels=1, window_size=(2, 2, 2)), core)

        feedback = actor.act(torch.tensor([3.0, 4.0, 0.0]))

        self.assertIsInstance(actor.actions, Actions)
        self.assertEqual(feedback, 5.0)
        self.assertTrue(torch.equal(actor.position, torch.tensor([3.0, 4.0, 0.0])))
        self.assertTrue(torch.equal(actor.velocity, torch.tensor([3.0, 4.0, 0.0])))


if __name__ == "__main__":
    unittest.main()
