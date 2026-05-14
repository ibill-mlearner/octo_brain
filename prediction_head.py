import torch
import torch.nn as nn


class PredictionHead(nn.Module):
    def __init__(self, channels: int):
        super().__init__()
        hidden = max(16, channels * 2)
        self.net = nn.Sequential(
            nn.Conv3d(channels * 2, hidden, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv3d(hidden, channels, kernel_size=1),
        )

    def forward(self, active: torch.Tensor, patch: torch.Tensor) -> torch.Tensor:
        return self.net(torch.cat([active, patch], dim=1))
