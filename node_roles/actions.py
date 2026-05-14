from dataclasses import dataclass
from typing import Dict

import torch

from tentacles.spatial_memory_system import SpatialMemorySystem


@dataclass
class ActionResult:
    """Outcome from applying one action to a node position."""

    position: torch.Tensor
    velocity: torch.Tensor
    feedback: float

    def to_message(self) -> Dict:
        return {
            "position": self.position.detach().cpu().tolist(),
            "velocity": self.velocity.detach().cpu().tolist(),
            "feedback": self.feedback,
        }


class Actions:
    """Action execution helper for actor-like nodes.

    Keeping execution in its own class leaves ActorNode focused on node state
    while this object grows into the place for richer action policies, safety
    checks, actuator adapters, and feedback shaping.
    """

    def __init__(self, core: SpatialMemorySystem):
        self.core = core

    def normalize(self, action: torch.Tensor, device: torch.device, dtype: torch.dtype) -> torch.Tensor:
        return action.detach().flatten().to(device=device, dtype=dtype)[:3]

    def execute(self, position: torch.Tensor, action: torch.Tensor) -> ActionResult:
        normalized = self.normalize(action, position.device, position.dtype)
        if normalized.numel() < 3:
            padded = torch.zeros(3, device=position.device, dtype=position.dtype)
            padded[: normalized.numel()] = normalized
            normalized = padded

        next_position = self.core._clamp_position(position + normalized)
        velocity = next_position - position
        feedback = float(torch.norm(velocity).item())
        return ActionResult(position=next_position, velocity=velocity, feedback=feedback)
