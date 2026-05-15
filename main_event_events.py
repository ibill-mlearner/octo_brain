"""Demo entrypoint for the async sensor event queue.

This root-level script stays thin and shows how the packaged event system is meant to be used. It builds the default desktop-sensor event system, starts it briefly, drains queued events, and prints compact summaries. The reusable queue, poller, event models, and sensor wiring all live in packages rather than in this runnable file. This keeps the demo easy to inspect while preserving the project structure for future event families.
"""

from __future__ import annotations

import asyncio

from events import build_default_sensor_event_system


async def run_demo() -> None:
    """Poll desktop sensors briefly while consuming queued events.

    The demo drains in short batches so it resembles an AI loop periodically checking for new sensor data.
    """

    event_system = build_default_sensor_event_system(interval_seconds=0.5)
    await event_system.start()

    try:
        print("async sensor event demo: collecting events for about 2 seconds")
        for _ in range(4):
            await asyncio.sleep(0.5)
            events = await event_system.queue.drain(
                max_events=10,
                timeout_seconds=0.05,
            )
            for event in events:
                reading_count = event.payload.get("reading_count", "-")
                print(
                    f"event#{event.sequence} "
                    f"type={event.event_type} "
                    f"source={event.source} "
                    f"readings={reading_count}"
                )
    finally:
        await event_system.stop()

    shutdown_events = await event_system.queue.drain(
        max_events=10,
        timeout_seconds=0.05,
    )
    for event in shutdown_events:
        print(
            f"event#{event.sequence} "
            f"type={event.event_type} "
            f"source={event.source}"
        )


def main() -> None:
    """Run the async sensor event queue demo.

    ``asyncio.run`` owns the event loop for this standalone script invocation.
    """

    asyncio.run(run_demo())


if __name__ == "__main__":
    main()
