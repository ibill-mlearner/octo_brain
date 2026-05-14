import random
from typing import Literal, Tuple

import torch
import torch.nn as nn


# Stability review notes from the reverted implementation:
#
# 1. LocalUpdateNet docstring note: I previously expanded this class comment
#    because the current demo runs the update network recurrently without any
#    optimizer step or learned calibration. My concern is that a randomly
#    initialized residual rule is being fed back into itself for hundreds of
#    steps, so even small positive feedback can accumulate. If this is a real
#    problem, the eventual fix should explain the intended stability contract of
#    this network here, but I have removed the behavioral change so the current
#    code remains exactly inspectable.
#
# 2. LocalUpdateNet constructor scale knobs: I added active_update_scale and
#    memory_update_scale as proposed controls for how strongly one recurrent
#    pass may alter the active window and memory field. The idea was not that
#    those exact numbers are correct, but that this layer may need explicit
#    step-size parameters if it is going to run as a continuous dynamical system.
#    Before applying that kind of fix, it is worth deciding whether stability
#    should come from fixed bounds, learned normalization, training, or some
#    other rule that better matches the spatial-memory design.
#
# 3. Storing the scale knobs on the module: I also stored those two scale values
#    on the LocalUpdateNet instance so the forward pass could use them every
#    step. The reason was to make the proposed recurrent update size part of the
#    model's configuration rather than an unexplained literal in forward(). If
#    this direction is accepted later, the names and defaults should probably be
#    documented as prototype safety rails rather than as a final learning rule.
#
# 4. Active-state delta bounding: I changed the active-state branch to pass the
#    raw to_active output through tanh before applying it as a residual. That was
#    meant to prevent a random convolution from emitting unbounded residuals into
#    the next active_state. The deeper question is whether active_state is meant
#    to be a bounded signal space at all; if not, tanh may be the wrong mechanism
#    even if it makes the demo numerically calmer.
#
# 5. Memory-delta bounding: I similarly bounded the to_delta output before it
#    was mixed into the memory patch. My hypothesis was that long-lived memory
#    should not receive arbitrarily large writes from an untrained local rule,
#    especially when those writes are immediately read again in later steps. The
#    fix should probably be revisited in terms of the intended memory semantics:
#    bounded cell values, sparse writes, normalization, decay, or trained write
#    gates may each imply different behavior.
#
# 6. Bounded active-state return: I wrapped active + active_delta in tanh in the
#    previous patch so the recurrent active window would remain inside a known
#    numeric interval. This is the most opinionated part of that attempted fix,
#    because it changes the representational range of the active window rather
#    than merely limiting one update. If the prototype depends on accumulating
#    magnitude over time, this would hide that behavior, so it should remain a
#    design note until the desired active-state range is clear.
#
# 7. SpatialMemorySystem memory_value_bound parameter: I added a configurable
#    memory_value_bound to the system constructor so the memory field could have
#    an explicit allowed value range. The motivation was that the demo output
#    looked like runaway feedback, and a spatial field that is continuously
#    rewritten may need a declared numeric envelope. Before implementing this,
#    we should decide whether the million-parameter field is supposed to behave
#    like normalized sensor space, free parameters, energy levels, or something
#    else.
#
# 8. Saving memory_value_bound on the system: I stored that bound on self so all
#    write paths could share one policy. The broader fix, if needed, should avoid
#    having separate hidden limits in write_patch(), step(), sensors, and actors.
#    A single system-level policy would make experiments easier to compare, but
#    only if the policy itself is agreed on first.
#
# 9. write_patch clamp: I clamped patch_body inside write_patch() so every direct
#    memory write would be constrained, not just writes that happen through
#    step(). The reason for putting the guard here was defensive: write_patch()
#    is the central mutation point for the memory field. However, that also means
#    callers could silently lose magnitude information, so if clamping is ever
#    added it may need logging, assertions, or a separate explicit normalization
#    call instead of an invisible clamp.
#
# 10. step pre-write clamp: I also clamped the computed patch + gate * delta in
#     step() before passing it into write_patch(). That was redundant with the
#     write_patch clamp, but it made the recurrent update's safety boundary more
#     visible at the call site. If a future implementation keeps a central write
#     bound, this extra clamp may be unnecessary; if the update rule itself needs
#     to be audited, an explicit bounded_patch variable may make that easier to
#     reason about.
#
# 11. Regression-test idea from the reverted patch: I added a test that ran many
#     recurrent steps and asserted the active state and memory field stayed finite
#     and within the chosen bounds. Since the behavioral fix is removed, that
#     exact test is removed too. The useful part of the idea is still worth
#     keeping in mind: once the intended stability mechanism is chosen, a small
#     repeated-step test should protect the demo from returning to massive error
#     values without forcing a specific implementation prematurely.


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
