"""Ordered async worker for spatial-memory kernel steps.

The worker is intentionally limited to runtime stepping: publish the requested
step, call the kernel, update the carried node state, and publish completion or
failure events. Prediction-error measurement, optimizer steps, and reflex
learning live in a separate subscriber module so production stepping can run
without training behavior attached.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import torch

from models.events import (
    KernelStepCompletedEvent,
    KernelStepFailedEvent,
    KernelStepRequestedEvent,
)
from tentacles.spatial_memory_system import SpatialMemorySystem

from ..async_event_queue import AsyncEventQueue


@dataclass
class KernelStepWorker:
    """Run ordered spatial-memory kernel steps and publish step events."""

    name: str
    memory: SpatialMemorySystem
    queue: AsyncEventQueue
    active_state: torch.Tensor
    position: torch.Tensor
    node_id: str | None = None
    kernel_id: str | None = None
    write_back: bool = True
    include_training_context: bool = False
    velocity: torch.Tensor = field(init=False)

    def __post_init__(self) -> None:
        """Place carried state on the memory device and initialize velocity."""

        device = self.memory.memory_field.device
        self.active_state = self.active_state.detach().to(device)
        self.position = self.position.detach().to(device)
        self.velocity = torch.zeros_like(self.position)

    async def run_steps(
        self,
        steps: int,
        stop_requested: asyncio.Event | None = None,
    ) -> None:
        """Run up to ``steps`` ordered kernel updates.

        ``stop_requested`` lets a runtime owner stop the loop between steps. The
        worker does not train, optimize, or choose reflex overrides; observers
        can subscribe to ``kernel.step.completed`` for that later behavior.
        """

        for step_index in range(steps):
            if stop_requested is not None and stop_requested.is_set():
                break

            await self.run_one_step(step_index=step_index)

    async def run_one_step(
        self,
        step_index: int,
    ) -> None:
        """Run one kernel step, update carried state, and publish lifecycle events."""

        current_position = self.position.detach()
        current_active_state = self.active_state.detach()

        await self.queue.publish_event(
            KernelStepRequestedEvent(
                source=self.name,
                step_index=step_index,
                node_id=self.node_id,
                kernel_id=self.kernel_id,
                current_position=current_position,
                write_back=self.write_back,
                tensor_summaries={"active_state": current_active_state},
            )
        )

        try:
            with torch.no_grad():
                updated_active, next_position, visible_patch = self.memory.step(
                    self.active_state,
                    self.position,
                    write_back=self.write_back,
                )
        except Exception as exc:  # noqa: BLE001 - kernel failures become events.
            await self.queue.publish_event(
                KernelStepFailedEvent(
                    source=self.name,
                    step_index=step_index,
                    node_id=self.node_id,
                    kernel_id=self.kernel_id,
                    current_position=current_position,
                    write_back=self.write_back,
                    error_summary={
                        "type": type(exc).__name__,
                        "message": str(exc),
                    },
                    tensor_summaries={"active_state": current_active_state},
                )
            )
            return

        self.velocity = (next_position - self.position).detach()
        self.position = next_position.detach()
        self.active_state = updated_active.detach()

        payload_extra = self._build_training_context(
            active_state=current_active_state,
            current_position=current_position,
            next_position=self.position,
            visible_patch=visible_patch.detach(),
        )

        completed_event = KernelStepCompletedEvent(
            source=self.name,
            step_index=step_index,
            node_id=self.node_id,
            kernel_id=self.kernel_id,
            current_position=current_position,
            next_position=self.position,
            write_back=self.write_back,
            tensor_summaries={
                "active_state": self.active_state,
                "visible_patch": visible_patch,
                "velocity": self.velocity,
            },
        )
        if payload_extra:
            completed_event.payload.update(payload_extra)

        await self.queue.publish_event(completed_event)

    def _build_training_context(
        self,
        active_state: torch.Tensor,
        current_position: torch.Tensor,
        next_position: torch.Tensor,
        visible_patch: torch.Tensor,
    ) -> dict[str, Any]:
        """Return optional in-process tensors for training subscribers.

        The default worker output stays summary-only. A caller that intentionally
        attaches the training observer may opt into this context without moving
        optimizer behavior into the worker itself.
        """

        if not self.include_training_context:
            return {}

        return {
            "training_context": {
                "active_state": active_state,
                "current_position": current_position,
                "next_position": next_position,
                "visible_patch": visible_patch,
                "velocity": self.velocity,
            }
        }
