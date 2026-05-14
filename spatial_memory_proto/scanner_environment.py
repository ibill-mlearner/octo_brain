# Parked experiment: this movement playground may be useful later, but node roles and
# the spatial memory core are the current focus of the prototype.
from dataclasses import dataclass, field
from typing import Iterable, List, Sequence, Tuple

Coordinate = Tuple[int, int, int]


@dataclass(frozen=True)
class ScannerConfig:
    field_size: Coordinate = (100, 100, 100)
    window_size: Coordinate = (10, 10, 10)
    stride: Coordinate = (10, 10, 10)

    @property
    def max_origin(self) -> Coordinate:
        return tuple(self.field_size[i] - self.window_size[i] for i in range(3))  # type: ignore[return-value]


@dataclass
class ScannerEnvironment:
    """Deterministic playground for scanner movement over spatial memory."""

    config: ScannerConfig = field(default_factory=ScannerConfig)
    position: Coordinate = (0, 0, 0)
    visited: List[Coordinate] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.position = self.clamp(self.position)
        self.visited.append(self.position)

    def clamp(self, position: Coordinate) -> Coordinate:
        max_origin = self.config.max_origin
        return tuple(max(0, min(position[i], max_origin[i])) for i in range(3))  # type: ignore[return-value]

    def move(self, delta: Coordinate) -> Coordinate:
        self.position = self.clamp(tuple(self.position[i] + delta[i] for i in range(3)))  # type: ignore[arg-type]
        self.visited.append(self.position)
        return self.position

    def move_to(self, position: Coordinate) -> Coordinate:
        self.position = self.clamp(position)
        self.visited.append(self.position)
        return self.position

    def path_to(self, goal: Coordinate, step: Coordinate | None = None) -> List[Coordinate]:
        """Build an axis-aligned path from the current scanner origin to a goal."""
        step = step or self.config.stride
        goal = self.clamp(goal)
        cursor = list(self.position)
        path: List[Coordinate] = []

        for axis in range(3):
            axis_step = max(1, abs(step[axis]))
            while cursor[axis] != goal[axis]:
                direction = 1 if goal[axis] > cursor[axis] else -1
                cursor[axis] += direction * min(axis_step, abs(goal[axis] - cursor[axis]))
                path.append(self.clamp(tuple(cursor)))  # type: ignore[arg-type]
        return path

    def follow(self, path: Iterable[Coordinate]) -> Coordinate:
        for point in path:
            self.move_to(point)
        return self.position

    def raster_scan(self, serpentine: bool = True) -> List[Coordinate]:
        """Return full-field scanner origins for the current field/window/stride."""
        sx, sy, sz = self.config.stride
        max_x, max_y, max_z = self.config.max_origin
        xs = list(range(0, max_x + 1, sx))
        ys = list(range(0, max_y + 1, sy))
        zs = list(range(0, max_z + 1, sz))

        origins: List[Coordinate] = []
        for z_index, z in enumerate(zs):
            y_order: Sequence[int] = ys if not (serpentine and z_index % 2) else tuple(reversed(ys))
            for y_index, y in enumerate(y_order):
                reverse_x = serpentine and ((y_index + z_index) % 2 == 1)
                x_order: Sequence[int] = xs if not reverse_x else tuple(reversed(xs))
                for x in x_order:
                    origins.append((x, y, z))
        return origins
