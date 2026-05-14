from dataclasses import dataclass
from typing import Tuple


@dataclass
class NodeConfig:
    """Configuration for a local node container inside spatial memory."""

    node_id: str
    role: str
    channels: int = 8
    field_size: Tuple[int, int, int] = (100, 100, 100)
    window_size: Tuple[int, int, int] = (10, 10, 10)
    learning_rate: float = 5e-4
