from dataclasses import replace
from typing import Any, Dict, Iterable, Mapping, Type

from tentacles.spatial_memory_system import SpatialMemorySystem

from .actor_node import ActorNode
from .base_node import BaseNode
from .decision_node import DecisionNode
from .node_config import NodeConfig
from .reflex_node import ReflexNode
from .sensor_node import SensorNode


class NodeRoleServer:
    """Small MCP-like registry/factory for node roles.

    The server exposes one general creation input (`role`) plus optional
    overrides for specific configuration. It is intentionally not an MCP server;
    it just uses the same hub-and-tools shape so callers can connect to one
    object, ask for a role, and then work deeper with the returned node object.
    """

    def __init__(self, core: SpatialMemorySystem, default_config: NodeConfig | None = None):
        self.core = core
        self.default_config = default_config or NodeConfig(
            node_id="node",
            role="base",
            channels=core.channels,
            field_size=core.field_size,
            window_size=core.window_size,
        )
        self._registry: Dict[str, Type[BaseNode]] = {}
        self.nodes: Dict[str, BaseNode] = {}
        self.register("base", BaseNode)
        self.register("sensor", SensorNode)
        self.register("reflex", ReflexNode)
        self.register("decision", DecisionNode)
        self.register("actor", ActorNode)
        self.register("act", ActorNode)

    def register(self, role: str, node_class: Type[BaseNode]) -> None:
        self._registry[role] = node_class

    def available_roles(self) -> Iterable[str]:
        return tuple(sorted(self._registry))

    def config_for(self, role: str, **overrides: Any) -> NodeConfig:
        config = replace(self.default_config, role=role, node_id=overrides.pop("node_id", f"{role}-1"))
        if overrides:
            config = replace(config, **overrides)
        return config

    def create(self, role: str, **overrides: Any) -> BaseNode:
        if role not in self._registry:
            raise ValueError(f"Unknown node role '{role}'. Available roles: {', '.join(self.available_roles())}")

        config = self.config_for(role, **overrides)
        node = self._registry[role](config, self.core)
        self.nodes[config.node_id] = node
        return node

    def connect(self, request: str | Mapping[str, Any], **overrides: Any) -> BaseNode:
        """Create a node from one role input plus optional specific fields.

        Examples:
            server.connect("sensor")
            server.connect("actor", node_id="arm-actor")
            server.connect({"role": "decision", "node_id": "planner"})
        """
        if isinstance(request, str):
            role = request
            config_overrides = overrides
        else:
            request_data = dict(request)
            role = request_data.pop("role")
            request_data.update(overrides)
            config_overrides = request_data

        return self.create(role, **config_overrides)

    def get(self, node_id: str) -> BaseNode:
        return self.nodes[node_id]
