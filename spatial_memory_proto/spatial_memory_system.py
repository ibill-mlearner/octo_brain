import random
from typing import Literal, Tuple

import torch
import torch.nn as nn


class LocalUpdateNet(nn.Module):
    """Local 3D rule network for active window updates."""

    def __init__(self, channels: int):
        super().__init__()
        hidden = max(16, channels * 2)
        self.net = nn.Sequential(
            nn.Conv3d(channels * 2, hidden, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv3d(hidden, hidden, kernel_size=1),
            nn.ReLU(),
        )
        self.to_active = nn.Conv3d(hidden, channels, kernel_size=1)
        self.to_delta = nn.Conv3d(hidden, channels, kernel_size=1)
        self.to_gate = nn.Conv3d(hidden, channels, kernel_size=1)
        self.to_move = nn.Sequential(
            nn.AdaptiveAvgPool3d(1), nn.Flatten(), nn.Linear(hidden, 3), nn.Tanh()
        )

    def forward(self, active: torch.Tensor, patch: torch.Tensor):
        h = self.net(torch.cat([active, patch], dim=1))
        return active + self.to_active(h), self.to_delta(h), torch.sigmoid(self.to_gate(h)), self.to_move(h)


class SpatialMemorySystem(nn.Module):
    def __init__(
        self,
        channels: int = 8,
        field_size: Tuple[int, int, int] = (100, 100, 100),
        window_size: Tuple[int, int, int] = (10, 10, 10),
        movement_mode: Literal["static", "random", "learned"] = "learned",
    ):
        super().__init__()
        self.channels = channels
        self.field_size = field_size
        self.window_size = window_size
        self.movement_mode = movement_mode
        self.memory_field = nn.Parameter(torch.zeros(channels, *field_size))
        nn.init.normal_(self.memory_field, mean=0.0, std=0.02)
        self.update_net = LocalUpdateNet(channels)

    def _clamp_position(self, position: torch.Tensor) -> torch.Tensor:
        max_xyz = torch.tensor(
            [self.field_size[i] - self.window_size[i] for i in range(3)],
            device=position.device,
            dtype=position.dtype,
        )
        min_xyz = torch.zeros_like(max_xyz)
        return torch.minimum(torch.maximum(position, min_xyz), max_xyz)

    def read_patch(self, position: torch.Tensor) -> torch.Tensor:
        x, y, z = [int(v) for v in position.tolist()]
        wx, wy, wz = self.window_size
        return self.memory_field[:, x : x + wx, y : y + wy, z : z + wz].unsqueeze(0)

    def mutable_inner_slices(self):
        """Slices for the cells a local node may rewrite inside its boundary wall."""
        if any(size <= 2 for size in self.window_size):
            return tuple(slice(0, size) for size in self.window_size)
        return tuple(slice(1, size - 1) for size in self.window_size)

    def write_patch(self, position: torch.Tensor, patch: torch.Tensor, preserve_boundary: bool = True) -> None:
        x, y, z = [int(v) for v in position.tolist()]
        wx, wy, wz = self.window_size
        patch_body = patch.squeeze(0)
        with torch.no_grad():
            target = self.memory_field[:, x : x + wx, y : y + wy, z : z + wz]
            if preserve_boundary:
                ix, iy, iz = self.mutable_inner_slices()
                target[:, ix, iy, iz].copy_(patch_body[:, ix, iy, iz])
            else:
                target.copy_(patch_body)

    def next_position(self, position: torch.Tensor, move_logits: torch.Tensor) -> torch.Tensor:
        if self.movement_mode == "static":
            return position
        if self.movement_mode == "random":
            offset = torch.tensor([random.choice([-1, 0, 1]) for _ in range(3)], device=position.device)
        else:
            offset = torch.round(move_logits.squeeze(0) * 2.0)
        return self._clamp_position(position + offset)

    def step(self, active_state: torch.Tensor, position: torch.Tensor, write_back: bool = True):
        patch = self.read_patch(position)
        updated_active, delta, gate, move_logits = self.update_net(active_state, patch)
        if write_back:
            self.write_patch(position, patch + gate * delta)
        return updated_active, self.next_position(position, move_logits), patch
