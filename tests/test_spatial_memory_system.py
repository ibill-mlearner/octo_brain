import sys
import unittest
from pathlib import Path

try:
    import torch
except ModuleNotFoundError:  # pragma: no cover - depends on local environment
    torch = None

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@unittest.skipIf(torch is None, "torch is not installed")
class SpatialMemorySystemTest(unittest.TestCase):
    def test_clamp_position_accepts_tensor_bounds_without_type_error(self):
        from tentacles.spatial_memory_system import SpatialMemorySystem

        memory = SpatialMemorySystem(channels=1, field_size=(100, 100, 100), window_size=(10, 10, 10))
        position = torch.tensor([-5.0, 50.0, 125.0])

        clamped = memory._clamp_position(position)

        self.assertTrue(torch.equal(clamped, torch.tensor([0.0, 50.0, 90.0])))

    def test_clamp_position_preserves_position_dtype(self):
        from tentacles.spatial_memory_system import SpatialMemorySystem

        memory = SpatialMemorySystem(channels=1, field_size=(100, 100, 100), window_size=(10, 10, 10))
        position = torch.tensor([-5.0, 50.0, 125.0], dtype=torch.float64)

        clamped = memory._clamp_position(position)

        self.assertEqual(clamped.dtype, torch.float64)


if __name__ == "__main__":
    unittest.main()
