from collections import deque
from typing import Deque
import random

import torch
import torch.nn as nn

from tentacles.spatial_memory_system import SpatialMemorySystem
from tentacles.prediction_head import PredictionHead
from tentacles.decision_module import DecisionModule


class AgentController(nn.Module):
    def __init__(self, memory: SpatialMemorySystem, error_threshold: float = 0.02, lr: float = 5e-4):
        super().__init__()
        self.memory = memory
        self.predictor = PredictionHead(memory.channels)
        self.decision = DecisionModule(memory.channels)
        self.error_threshold = error_threshold
        self.error_buffer: Deque[float] = deque(maxlen=64)
        self.position = torch.zeros(3)
        self.velocity = torch.zeros(3)
        self.active_state = torch.zeros(1, memory.channels, *memory.window_size)
        self.optim = torch.optim.Adam(self.parameters(), lr=lr)

    def _to_device(self):
        d = self.memory.memory_field.device
        self.position = self.position.to(d)
        self.velocity = self.velocity.to(d)
        self.active_state = self.active_state.to(d)

    def reflex_override(self) -> torch.Tensor:
        mode = random.choice(["stop", "reverse", "random"])
        if mode == "stop":
            return torch.zeros_like(self.velocity)
        if mode == "reverse":
            return -self.velocity.clamp(min=-1, max=1)
        return torch.tensor([random.choice([-1.0, 0.0, 1.0]) for _ in range(3)], device=self.velocity.device)

    def run_episode(self, steps: int = 500, log_every: int = 50):
        self.train()
        self._to_device()
        logs = []

        for step in range(steps):
            patch = self.memory.read_patch(self.position)
            predicted_next_patch = self.predictor(self.active_state, patch)

            action = torch.round(self.decision(self.active_state, torch.tensor(0.0, device=patch.device), self.velocity))
            next_position = self.memory._clamp_position(self.position + action)
            next_patch = self.memory.read_patch(next_position)
            error = (predicted_next_patch - next_patch).pow(2).mean()
            error_value = float(error.detach().item())
            self.error_buffer.append(error_value)

            reflex = False
            if error_value > self.error_threshold:
                reflex = True
                action = self.reflex_override()
                next_position = self.memory._clamp_position(self.position + action)

            self.optim.zero_grad()
            error.backward()
            self.optim.step()

            updated_active, _, visible_patch = self.memory.step(self.active_state, self.position, write_back=False)
            self.memory.write_patch(self.position, visible_patch + 0.2 * (predicted_next_patch.detach() - visible_patch))

            self.velocity = (next_position - self.position).detach()
            self.position = next_position.detach()
            self.active_state = updated_active.detach()

            item = {"step": step, "position": tuple(int(v) for v in self.position.tolist()), "error": error_value, "reflex": reflex}
            logs.append(item)
            if step % log_every == 0 or reflex:
                print(f"step={step:03d} role=agent error={error_value:.5f} reflex={reflex}")

        return logs
