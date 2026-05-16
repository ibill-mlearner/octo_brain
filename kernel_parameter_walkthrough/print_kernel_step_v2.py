"""Print SpatialMemorySystem parameters, then take one visible kernel step."""

from pathlib import Path
import sys

import numpy as np
import torch

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tentacles.spatial_memory_system import SpatialMemorySystem


def print_array_summary(
    label: str,
    values: np.ndarray,
) -> None:
    """Print compact shape, statistics, and preview data for one array."""
    preview = values.reshape(-1)[:20]

    print(f"\n{label}")
    print(f"  shape={values.shape}")
    print(f"  dtype={values.dtype}")
    print(f"  elements={values.size}")
    print(f"  min={values.min():+.6f}")
    print(f"  max={values.max():+.6f}")
    print(f"  mean={values.mean():+.6f}")
    print(f"  std={values.std():+.6f}")
    print(f"  preview={preview}")


def main() -> None:
    """Create the moving spatial-memory kernel, inspect it, and step once."""
    torch.manual_seed(0)
    np.set_printoptions(precision=5, suppress=True, threshold=200)

    core = SpatialMemorySystem(
        channels=8,
        field_size=(100, 100, 100),
        window_size=(10, 10, 10),
        movement_mode="learned",
    )

    print("SpatialMemorySystem parameters before stepping")
    for name, parameter in core.named_parameters():
        values = parameter.detach().cpu().numpy()
        print_array_summary(name, values)

    active_state = torch.zeros(
        1,
        core.channels,
        *core.window_size,
    )
    position = torch.tensor(
        [45.0, 45.0, 45.0],
        dtype=torch.float32,
    )

    updated_active, next_position, starting_patch = core.step(
        active_state,
        position,
        write_back=True,
    )
    written_patch = core.read_patch(position)

    print("\nOne learned kernel step")
    print(f"  start_position={position.detach().cpu().numpy()}")
    print(f"  next_position={next_position.detach().cpu().numpy()}")
    print_array_summary(
        "starting_patch",
        starting_patch.detach().cpu().numpy(),
    )
    print_array_summary(
        "updated_active_state",
        updated_active.detach().cpu().numpy(),
    )
    print_array_summary(
        "written_patch_after_step",
        written_patch.detach().cpu().numpy(),
    )


if __name__ == "__main__":
    main()
