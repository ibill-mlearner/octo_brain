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

    from decision_module import DecisionModule
    from prediction_head import PredictionHead
    from spatial_memory_system import LocalUpdateNet, SpatialMemorySystem


@unittest.skipIf(torch is None, "torch is not installed")
class GpuBasicsTest(unittest.TestCase):
    def target_device(self):
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def test_cuda_tensor_round_trip_when_gpu_is_available(self):
        if not torch.cuda.is_available():
            self.skipTest("CUDA GPU is not available")

        cpu_values = torch.tensor([1.0, 2.0, 3.0])
        gpu_values = cpu_values.to("cuda")
        returned = (gpu_values + 1.0).to("cpu")

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

        self.assertEqual(memory.memory_field.device, device)
        self.assertEqual(patch.device, device)
        self.assertEqual(updated_active.device, device)
        self.assertEqual(next_position.device, device)
        self.assertEqual(visible_patch.device, device)
        self.assertEqual(tuple(patch.shape), (1, 2, 3, 3, 3))
        self.assertEqual(tuple(updated_active.shape), tuple(active_state.shape))
        self.assertEqual(tuple(next_position.shape), (3,))
        self.assertEqual(visible_patch.dtype, memory.memory_field.dtype)

    def test_local_update_net_outputs_match_input_tensor_contract(self):
        device = self.target_device()
        net = LocalUpdateNet(channels=3).to(device)
        active = torch.zeros(1, 3, 4, 4, 4, device=device)
        patch = torch.ones(1, 3, 4, 4, 4, device=device)

        updated_active, delta, gate, move_logits = net(active, patch)

        self.assertEqual(updated_active.device, device)
        self.assertEqual(delta.device, device)
        self.assertEqual(gate.device, device)
        self.assertEqual(move_logits.device, device)
        self.assertEqual(tuple(updated_active.shape), tuple(active.shape))
        self.assertEqual(tuple(delta.shape), tuple(active.shape))
        self.assertEqual(tuple(gate.shape), tuple(active.shape))
        self.assertEqual(tuple(move_logits.shape), (1, 3))
        self.assertEqual(updated_active.dtype, active.dtype)
        self.assertEqual(delta.dtype, active.dtype)
        self.assertEqual(gate.dtype, active.dtype)
        self.assertEqual(move_logits.dtype, active.dtype)
        self.assertTrue(bool(torch.all(gate >= 0.0).detach().cpu().item()))
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

        self.assertEqual(predicted_patch.device, device)
        self.assertEqual(action.device, device)
        self.assertEqual(tuple(predicted_patch.shape), tuple(patch.shape))
        self.assertEqual(tuple(action.shape), (3,))
        self.assertEqual(predicted_patch.dtype, active.dtype)
        self.assertEqual(action.dtype, active.dtype)


if __name__ == "__main__":
    unittest.main()
