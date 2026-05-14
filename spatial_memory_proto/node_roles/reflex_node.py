from .base_node import BaseNode


class ReflexNode(BaseNode):
    """Immediate urgency path for danger, high error, or slow decisions."""

    def check(self, error: float, threshold: float = 0.02):
        urgency = min(1.0, error / max(threshold, 1e-6))
        trigger = error > threshold
        return trigger, urgency
