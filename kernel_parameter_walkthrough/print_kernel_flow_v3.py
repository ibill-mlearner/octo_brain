"""Explore multi-axis SpatialMemorySystem movement formulas."""

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
    preview = values.reshape(-1)[:12]

    print(f"\n{label}")
    print(f"  shape={values.shape}")
    print(f"  dtype={values.dtype}")
    print(f"  elements={values.size}")
    print(f"  min={values.min():+.6f}")
    print(f"  max={values.max():+.6f}")
    print(f"  mean={values.mean():+.6f}")
    print(f"  std={values.std():+.6f}")
    print(f"  preview={preview}")


def clamp_position(
    position: np.ndarray,
    max_origin: np.ndarray,
) -> np.ndarray:
    """Keep a floating point xyz origin inside the readable memory field."""
    return np.minimum(
        np.maximum(position, np.zeros_like(max_origin)),
        max_origin,
    )


def wrap_position(
    position: np.ndarray,
    max_origin: np.ndarray,
) -> np.ndarray:
    """Wrap a flowing xyz origin so movement keeps circulating through space."""
    return np.mod(position, max_origin + 1.0)


def bounce_position(
    position: np.ndarray,
    max_origin: np.ndarray,
) -> np.ndarray:
    """Reflect a flowing xyz origin at each wall instead of stopping there."""
    period = max_origin * 2.0
    wrapped = np.mod(position, period)
    return max_origin - np.abs(wrapped - max_origin)


def difference_velocity(
    scalars: np.ndarray,
) -> np.ndarray:
    """Turn xyz scalars into a coupled difference flow vector."""
    x_scalar, y_scalar, z_scalar = scalars
    return np.array(
        [
            x_scalar - y_scalar,
            y_scalar - z_scalar,
            z_scalar - x_scalar,
        ],
        dtype=np.float32,
    )


def coupled_wave_offset(
    step_index: int,
    scalars: np.ndarray,
) -> np.ndarray:
    """Create a small curved offset so every step is not a straight line."""
    phase = step_index * 0.5
    x_scalar, y_scalar, z_scalar = scalars
    return np.array(
        [
            np.sin(phase * x_scalar),
            np.cos(phase * y_scalar),
            np.sin(phase * z_scalar + phase),
        ],
        dtype=np.float32,
    )


def print_formula_path(
    label: str,
    formula: str,
    positions: np.ndarray,
) -> None:
    """Print one named xyz path as compact integer origins."""
    print(f"\n{label}")
    print(f"  formula={formula}")
    for step_index, position in enumerate(positions):
        xyz = position.astype(np.int64)
        print(f"  t={step_index:02d} origin=({xyz[0]:02d}, {xyz[1]:02d}, {xyz[2]:02d})")


def build_linear_flow(
    start: np.ndarray,
    velocity: np.ndarray,
    max_origin: np.ndarray,
    step_count: int,
) -> np.ndarray:
    """Build p(t) = bounce(start + t * velocity) for simultaneous xyz motion."""
    points = []
    for step_index in range(step_count):
        raw_position = start + step_index * velocity
        points.append(bounce_position(raw_position, max_origin))
    return np.asarray(points, dtype=np.float32)


def build_difference_flow(
    start: np.ndarray,
    scalars: np.ndarray,
    max_origin: np.ndarray,
    step_count: int,
) -> np.ndarray:
    """Build p(t) from xyz scalar differences plus a bounded curved offset."""
    points = []
    velocity = difference_velocity(scalars)
    for step_index in range(step_count):
        raw_position = start + step_index * velocity + coupled_wave_offset(
            step_index,
            scalars,
        )
        points.append(wrap_position(raw_position, max_origin))
    return np.asarray(points, dtype=np.float32)


def inspect_patch_along_path(
    core: SpatialMemorySystem,
    label: str,
    positions: np.ndarray,
) -> None:
    """Read spatial-memory patches along a proposed movement path."""
    print(f"\nPatch observations for {label}")
    for step_index, position in enumerate(positions):
        tensor_position = torch.tensor(
            position.astype(np.float32),
            dtype=torch.float32,
        )
        patch = core.read_patch(tensor_position)
        patch_values = patch.detach().cpu().numpy()
        print(
            f"  t={step_index:02d} "
            f"origin={tuple(position.astype(np.int64))} "
            f"patch_mean={patch_values.mean():+.6f} "
            f"patch_std={patch_values.std():+.6f}"
        )


def main() -> None:
    """Print v3 formulas for faster coupled xyz movement through memory."""
    torch.manual_seed(0)
    np.set_printoptions(precision=5, suppress=True, threshold=200)

    core = SpatialMemorySystem(
        channels=8,
        field_size=(100, 100, 100),
        window_size=(10, 10, 10),
        movement_mode="learned",
    )

    max_origin = np.array(
        [
            core.field_size[0] - core.window_size[0],
            core.field_size[1] - core.window_size[1],
            core.field_size[2] - core.window_size[2],
        ],
        dtype=np.float32,
    )
    start = np.array([10.0, 10.0, 10.0], dtype=np.float32)
    scalar_flow = np.array([2.0, 3.0, 5.0], dtype=np.float32)
    step_count = 12

    linear_positions = build_linear_flow(
        start,
        scalar_flow,
        max_origin,
        step_count,
    )
    difference_positions = build_difference_flow(
        start,
        scalar_flow,
        max_origin,
        step_count,
    )

    print("SpatialMemorySystem v3 coupled xyz movement formulas")
    print(f"  max_origin={max_origin.astype(np.int64)}")
    print(f"  start={start.astype(np.int64)}")
    print(f"  xyz_scalars={scalar_flow.astype(np.int64)}")
    print(
        "  constant_flow: p(t) = bounce(start + t * [2, 3, 5]) "
        "so x, y, and z move together every step."
    )
    print(
        "  difference_flow: p(t) = wrap(start + t * [2-3, 3-5, 5-2] + wave(t)) "
        "so scalar differences create diagonal drift."
    )

    print_formula_path(
        "constant_flow_path",
        "bounce(start + t * [2, 3, 5])",
        linear_positions,
    )
    print_formula_path(
        "difference_flow_path",
        "wrap(start + t * [-1, -2, 3] + wave(t))",
        difference_positions,
    )

    inspect_patch_along_path(
        core,
        "constant_flow_path",
        linear_positions,
    )
    inspect_patch_along_path(
        core,
        "difference_flow_path",
        difference_positions,
    )
    print_array_summary(
        "memory_field_after_formula_observation",
        core.memory_field.detach().cpu().numpy(),
    )


if __name__ == "__main__":
    main()
