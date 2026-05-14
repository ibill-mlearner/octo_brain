import importlib.util
import unittest


torch_spec = importlib.util.find_spec("torch")
if torch_spec is None:
    torch = None
else:
    import torch


@unittest.skipIf(torch is None, "torch is not installed")
class GpuBasicsTest(unittest.TestCase):
    def test_cuda_tensor_round_trip_when_gpu_is_available(self):
        if not torch.cuda.is_available():
            self.skipTest("CUDA GPU is not available")

        cpu_values = torch.tensor([1.0, 2.0, 3.0])
        gpu_values = cpu_values.to("cuda")
        returned = (gpu_values + 1.0).to("cpu")

        self.assertTrue(torch.equal(returned, torch.tensor([2.0, 3.0, 4.0])))


if __name__ == "__main__":
    unittest.main()
