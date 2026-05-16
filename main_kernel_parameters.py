"""Print inspectable SpatialMemorySystem parameter arrays."""

import numpy as np
import torch

from tentacles.spatial_memory_system import SpatialMemorySystem


def main() -> None:
    """Create the moving spatial-memory kernel and print its parameters."""
    torch.manual_seed(0)
    np.set_printoptions(precision=5, suppress=True, threshold=200)

    core = SpatialMemorySystem(
        channels=8,
        field_size=(100, 100, 100),
        window_size=(10, 10, 10),
        movement_mode="learned",
    )

    for name, parameter in core.named_parameters():
        values = parameter.detach().cpu().numpy()
        preview = values.reshape(-1)[:20]

        print(f"\n{name}")
        print(f"  shape={values.shape}")
        print(f"  dtype={values.dtype}")
        print(f"  elements={values.size}")
        print(f"  min={values.min():+.6f}")
        print(f"  max={values.max():+.6f}")
        print(f"  mean={values.mean():+.6f}")
        print(f"  std={values.std():+.6f}")
        print(f"  preview={preview}")


if __name__ == "__main__":
    main()
