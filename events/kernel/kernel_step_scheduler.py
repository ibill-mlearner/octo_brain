"""Reusable scheduler for publishing kernel-step request events.

The scheduler owns only orchestration metadata: how many step requests should be
published, where each request starts, which position should follow it when that
is known, and whether the eventual kernel runner should write back into
persistent memory. It does not execute ``SpatialMemorySystem.step`` and does not
mutate the memory field.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

import torch

from models.events import BaseEvent
from models.events.kernel import KernelStepRequestedEvent

from events.async_event_queue import AsyncEventQueue


PositionInput = Any


class KernelMovementModel(Protocol):
    """Minimal movement surface shared with ``SpatialMemorySystem``."""

    def next_position(
        self,
        position: torch.Tensor,
        move_logits: torch.Tensor,
    ) -> torch.Tensor:
        """Return the next readable kernel origin for a proposed movement."""

        ...


@dataclass(frozen=True)
class KernelStepSchedule:
    """Input bundle describing a sequence of kernel-step requests."""

    step_count: int
    start_position: PositionInput | None = None
    path: Iterable[PositionInput] | None = None
    write_back: bool = True
    node_id: str | None = None
    kernel_id: str | None = None
    source: str = "kernel_step_scheduler"

    def __post_init__(self) -> None:
        """Validate the fixed schedule length before publishing begins."""

        if self.step_count < 0:
            raise ValueError("step_count must be greater than or equal to zero")


class KernelStepScheduler:
    """Publish ``kernel.step.requested`` events for a planned kernel walk."""

    def __init__(
        self,
        event_queue: AsyncEventQueue,
        source: str = "kernel_step_scheduler",
    ) -> None:
        """Store the target queue and default event source label."""

        self.event_queue = event_queue
        self.source = source

    async def publish_steps(
        self,
        step_count: int,
        start_position: PositionInput | None = None,
        path: Iterable[PositionInput] | None = None,
        write_back: bool = True,
        movement_model: KernelMovementModel | None = None,
        move_logits: PositionInput | None = None,
        node_id: str | None = None,
        kernel_id: str | None = None,
        source: str | None = None,
    ) -> list[BaseEvent]:
        """Publish a fixed number of kernel-step request events.

        ``path`` is authoritative when supplied: each event uses the matching
        path position as its current position, and the following path element as
        ``next_position`` when available. Without a path, the scheduler starts at
        ``start_position`` or the origin and advances through ``movement_model``
        using its ``next_position`` method, mirroring the movement doorway used
        by ``SpatialMemorySystem``.
        """

        schedule = KernelStepSchedule(
            step_count=step_count,
            start_position=start_position,
            path=path,
            write_back=write_back,
            node_id=node_id,
            kernel_id=kernel_id,
            source=source or self.source,
        )
        positions = self._build_positions(
            schedule=schedule,
            movement_model=movement_model,
            move_logits=move_logits,
        )

        published_events: list[BaseEvent] = []
        for step_index in range(schedule.step_count):
            current_position = positions[step_index]
            next_position = self._next_path_position(
                positions=positions,
                step_index=step_index,
            )
            published_events.append(
                await self.event_queue.publish_event(
                    KernelStepRequestedEvent(
                        source=schedule.source,
                        step_index=step_index,
                        node_id=schedule.node_id,
                        kernel_id=schedule.kernel_id,
                        current_position=current_position,
                        next_position=next_position,
                        write_back=schedule.write_back,
                    )
                )
            )

        return published_events

    def _build_positions(
        self,
        schedule: KernelStepSchedule,
        movement_model: KernelMovementModel | None,
        move_logits: PositionInput | None,
    ) -> list[PositionInput]:
        """Return current positions plus an optional final look-ahead point."""

        if schedule.path is not None:
            return self._coerce_path(
                path=schedule.path,
                step_count=schedule.step_count,
            )

        position = self._as_position_tensor(schedule.start_position)
        positions: list[PositionInput] = [position]
        while len(positions) < schedule.step_count + 1:
            position = self._advance_position(
                position=position,
                movement_model=movement_model,
                move_logits=move_logits,
            )
            positions.append(position)

        return positions

    def _advance_position(
        self,
        position: torch.Tensor,
        movement_model: KernelMovementModel | None,
        move_logits: PositionInput | None,
    ) -> torch.Tensor:
        """Advance through the supplied movement model or remain stationary."""

        if movement_model is None:
            return position.clone()

        return movement_model.next_position(
            position,
            self._as_move_logits(
                move_logits=move_logits,
                position=position,
            ),
        )

    def _coerce_path(
        self,
        path: Iterable[PositionInput],
        step_count: int,
    ) -> list[PositionInput]:
        """Materialize and validate an externally supplied position path."""

        positions = list(path)
        if len(positions) < step_count:
            raise ValueError(
                "path must contain at least step_count positions"
            )

        return positions

    def _next_path_position(
        self,
        positions: Sequence[PositionInput],
        step_index: int,
    ) -> PositionInput | None:
        """Return the following position when the schedule can name one."""

        next_index = step_index + 1
        if next_index >= len(positions):
            return None

        return positions[next_index]

    def _as_position_tensor(
        self,
        position: PositionInput | None,
    ) -> torch.Tensor:
        """Normalize optional starting coordinates into an xyz tensor."""

        if position is None:
            return torch.zeros(
                3,
                dtype=torch.float32,
            )

        return torch.as_tensor(
            position,
            dtype=torch.float32,
        )

    def _as_move_logits(
        self,
        move_logits: PositionInput | None,
        position: torch.Tensor,
    ) -> torch.Tensor:
        """Normalize movement logits for ``SpatialMemorySystem.next_position``."""

        if move_logits is None:
            return torch.zeros(
                1,
                3,
                device=position.device,
                dtype=position.dtype,
            )

        logits = torch.as_tensor(
            move_logits,
            device=position.device,
            dtype=position.dtype,
        )
        if logits.shape == (3,):
            return logits.unsqueeze(0)

        return logits


async def publish_kernel_step_requests(
    event_queue: AsyncEventQueue,
    step_count: int,
    start_position: PositionInput | None = None,
    path: Iterable[PositionInput] | None = None,
    write_back: bool = True,
    movement_model: KernelMovementModel | None = None,
    move_logits: PositionInput | None = None,
    node_id: str | None = None,
    kernel_id: str | None = None,
    source: str = "kernel_step_scheduler",
) -> list[BaseEvent]:
    """Convenience wrapper for one-off kernel-step request schedules."""

    scheduler = KernelStepScheduler(
        event_queue=event_queue,
        source=source,
    )
    return await scheduler.publish_steps(
        step_count=step_count,
        start_position=start_position,
        path=path,
        write_back=write_back,
        movement_model=movement_model,
        move_logits=move_logits,
        node_id=node_id,
        kernel_id=kernel_id,
    )
