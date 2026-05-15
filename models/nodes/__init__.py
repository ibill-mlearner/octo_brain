"""Node models for structured node state snapshots."""

from .actor_node import ActorNodeModel
from .base_node import BaseNodeModel
from .decision_node import DecisionNodeModel
from .reflex_node import ReflexNodeModel
from .sensor_node import SensorNodeModel

DEFAULT_NODE_MODELS = (
    SensorNodeModel(node_id="sensor"),
    ReflexNodeModel(node_id="reflex"),
    DecisionNodeModel(node_id="decision"),
    ActorNodeModel(node_id="actor"),
)

__all__ = [
    "ActorNodeModel",
    "BaseNodeModel",
    "DecisionNodeModel",
    "DEFAULT_NODE_MODELS",
    "ReflexNodeModel",
    "SensorNodeModel",
]
