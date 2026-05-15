import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

torch_spec = importlib.util.find_spec("torch")
if torch_spec is None:
    torch = None
else:
    import torch

    sys.path.insert(0, str(ROOT))

    from tentacles.decision_module import DecisionModule
    from tentacles.prediction_head import PredictionHead
    from tentacles.spatial_memory_system import LocalUpdateNet, SpatialMemorySystem


@unittest.skipIf(torch is None, "torch is not installed")
class GpuBasicsTest(unittest.TestCase):
    def target_device(self):
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def assertSameDevice(self, actual, expected):
        """Treat ``cuda`` and the default ``cuda:0`` tensor device as equivalent."""
        actual_device = torch.device(actual)
        expected_device = torch.device(expected)

        # This is what I expect to happen, actual_device.type should equal expected_device.type.
        self.assertEqual(actual_device.type, expected_device.type)
        if expected_device.type != "cuda":
            # This is what I expect to happen, actual_device.index should equal expected_device.index.
            self.assertEqual(actual_device.index, expected_device.index)
            return

        expected_index = expected_device.index
        if expected_index is None:
            expected_index = torch.cuda.current_device()
        # This is what I expect to happen, actual_device.index should equal expected_index.
        self.assertEqual(actual_device.index, expected_index)

    def test_cuda_tensor_round_trip_when_gpu_is_available(self):
        if not torch.cuda.is_available():
            self.skipTest("CUDA GPU is not available")

        cpu_values = torch.tensor([1.0, 2.0, 3.0])
        gpu_values = cpu_values.to("cuda")
        returned = (gpu_values + 1.0).to("cpu")

        # This is what I expect to happen, torch.equal(returned, torch.tensor([2.0, 3.0, 4.0])) should evaluate as true.
        self.assertTrue(torch.equal(returned, torch.tensor([2.0, 3.0, 4.0])))

    def test_memory_system_tensors_stay_on_target_device(self):
        device = self.target_device()
        memory = SpatialMemorySystem(
            channels=2,
            field_size=(6, 6, 6),
            window_size=(3, 3, 3),
            movement_mode="static",
        ).to(device)
        position = torch.tensor([1.0, 1.0, 1.0], device=device)
        active_state = torch.zeros(1, 2, 3, 3, 3, device=device)

        patch = memory.read_patch(position)
        updated_active, next_position, visible_patch = memory.step(active_state, position, write_back=False)

        # This is what I expect to happen, memory.memory_field.device should stay on the same device as device.
        self.assertSameDevice(memory.memory_field.device, device)
        # This is what I expect to happen, patch.device should stay on the same device as device.
        self.assertSameDevice(patch.device, device)
        # This is what I expect to happen, updated_active.device should stay on the same device as device.
        self.assertSameDevice(updated_active.device, device)
        # This is what I expect to happen, next_position.device should stay on the same device as device.
        self.assertSameDevice(next_position.device, device)
        # This is what I expect to happen, visible_patch.device should stay on the same device as device.
        self.assertSameDevice(visible_patch.device, device)
        # This is what I expect to happen, tuple(patch.shape) should equal (1, 2, 3, 3, 3).
        self.assertEqual(tuple(patch.shape), (1, 2, 3, 3, 3))
        # This is what I expect to happen, tuple(updated_active.shape) should equal tuple(active_state.shape).
        self.assertEqual(tuple(updated_active.shape), tuple(active_state.shape))
        # This is what I expect to happen, tuple(next_position.shape) should equal (3,).
        self.assertEqual(tuple(next_position.shape), (3,))
        # This is what I expect to happen, visible_patch.dtype should equal memory.memory_field.dtype.
        self.assertEqual(visible_patch.dtype, memory.memory_field.dtype)

    def test_local_update_net_outputs_match_input_tensor_contract(self):
        device = self.target_device()
        net = LocalUpdateNet(channels=3).to(device)
        active = torch.zeros(1, 3, 4, 4, 4, device=device)
        patch = torch.ones(1, 3, 4, 4, 4, device=device)

        updated_active, delta, gate, move_logits = net(active, patch)

        # This is what I expect to happen, updated_active.device should stay on the same device as device.
        self.assertSameDevice(updated_active.device, device)
        # This is what I expect to happen, delta.device should stay on the same device as device.
        self.assertSameDevice(delta.device, device)
        # This is what I expect to happen, gate.device should stay on the same device as device.
        self.assertSameDevice(gate.device, device)
        # This is what I expect to happen, move_logits.device should stay on the same device as device.
        self.assertSameDevice(move_logits.device, device)
        # This is what I expect to happen, tuple(updated_active.shape) should equal tuple(active.shape).
        self.assertEqual(tuple(updated_active.shape), tuple(active.shape))
        # This is what I expect to happen, tuple(delta.shape) should equal tuple(active.shape).
        self.assertEqual(tuple(delta.shape), tuple(active.shape))
        # This is what I expect to happen, tuple(gate.shape) should equal tuple(active.shape).
        self.assertEqual(tuple(gate.shape), tuple(active.shape))
        # This is what I expect to happen, tuple(move_logits.shape) should equal (1, 3).
        self.assertEqual(tuple(move_logits.shape), (1, 3))
        # This is what I expect to happen, updated_active.dtype should equal active.dtype.
        self.assertEqual(updated_active.dtype, active.dtype)
        # This is what I expect to happen, delta.dtype should equal active.dtype.
        self.assertEqual(delta.dtype, active.dtype)
        # This is what I expect to happen, gate.dtype should equal active.dtype.
        self.assertEqual(gate.dtype, active.dtype)
        # This is what I expect to happen, move_logits.dtype should equal active.dtype.
        self.assertEqual(move_logits.dtype, active.dtype)
        # This is what I expect to happen, bool(torch.all(gate >= 0.0).detach().cpu().item()) should evaluate as true.
        self.assertTrue(bool(torch.all(gate >= 0.0).detach().cpu().item()))
        # This is what I expect to happen, bool(torch.all(gate <= 1.0).detach().cpu().item()) should evaluate as true.
        self.assertTrue(bool(torch.all(gate <= 1.0).detach().cpu().item()))

    def test_prediction_and_decision_heads_return_expected_tensor_shapes(self):
        device = self.target_device()
        channels = 2
        active = torch.zeros(1, channels, 3, 3, 3, device=device)
        patch = torch.ones(1, channels, 3, 3, 3, device=device)
        error_scalar = torch.tensor(0.25, device=device)
        velocity = torch.tensor([1.0, 0.0, -1.0], device=device)
        predictor = PredictionHead(channels).to(device)
        decision = DecisionModule(channels).to(device)

        predicted_patch = predictor(active, patch)
        action = decision(active, error_scalar, velocity)

        # This is what I expect to happen, predicted_patch.device should stay on the same device as device.
        self.assertSameDevice(predicted_patch.device, device)
        # This is what I expect to happen, action.device should stay on the same device as device.
        self.assertSameDevice(action.device, device)
        # This is what I expect to happen, tuple(predicted_patch.shape) should equal tuple(patch.shape).
        self.assertEqual(tuple(predicted_patch.shape), tuple(patch.shape))
        # This is what I expect to happen, tuple(action.shape) should equal (3,).
        self.assertEqual(tuple(action.shape), (3,))
        # This is what I expect to happen, predicted_patch.dtype should equal active.dtype.
        self.assertEqual(predicted_patch.dtype, active.dtype)
        # This is what I expect to happen, action.dtype should equal active.dtype.
        self.assertEqual(action.dtype, active.dtype)


if __name__ == "__main__":
    unittest.main()
