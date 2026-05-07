import torch
import torch.nn as nn


class DecisionModule(nn.Module):
    def __init__(self, channels: int):
        super().__init__()
        self.pool = nn.AdaptiveAvgPool3d(1)
        self.mlp = nn.Sequential(
            nn.Linear(channels + 4, 32),
            nn.ReLU(),
            nn.Linear(32, 3),
            nn.Tanh(),
        )

    def forward(self, active: torch.Tensor, error_scalar: torch.Tensor, velocity: torch.Tensor) -> torch.Tensor:
        pooled = self.pool(active).flatten(1)
        x = torch.cat([pooled, error_scalar.view(1, 1), velocity.view(1, 3)], dim=1)
        return self.mlp(x).squeeze(0)
