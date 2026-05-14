# Spatial Memory Prototype

This prototype is exploring a very small, always-running AI object built from spatial parameters instead of a normal stack of matrix multiplications.

## Core mental model

- The large **100x100x100 memory field** is the AI object. At one scalar per cell, that is **1,000,000 saved parameters**.
- Those saved parameters are the long-lived memory. The model reads them spatially as a field, not as a flattened matrix-multiply layer.
- A smaller node window moves through that field. In the current code this is a **10x10x10 active window**, but the design idea is a small node container living anywhere inside the larger million-parameter container.
- The outer wall of the node window is treated as the contact boundary with the larger memory field. Boundary cells should be read as context/pressure from the outside, while the inner cells are the part a node is allowed to rewrite while it is learning.
- Learning happens by continuously scanning, sensing, and rewriting local inner cells. The system should be thought of as always processing and always changing, not as a separate offline training pass followed by frozen inference.

## Node roles are the focus

The node role layer is the main design surface right now.

### Base node

`BaseNode` owns the common state for a moving local container: position, velocity, active window state, device placement, and message serialization. Other nodes should build from this rather than each inventing their own state shape.

### Sensor node

A sensor node should accept raw numeric readings from attached sensors: camera bytes/pixels, pressure values, temperature values, internal body signals, or any other plain-number stream.

The goal is **not** to parse high-level concepts before the model sees the data. A camera should not first become labels or language tokens. Its raw numbers should be placed into the active node window so the spatial memory system can process them directly.

### Reflex node

A reflex node exists for immediate reaction. It should be able to trigger from urgency, high error, danger-like signals, timeout pressure, or extreme actor sensations before the slower group decision process finishes.

This is the quick path: if decision-making is taking too long, the reflex node can still force a simple immediate response.

### Decision node

A decision node is the coordination layer. Sensor nodes and actor nodes can report preferences, errors, urgency, and feedback. The decision node should eventually arbitrate those messages and tell actor nodes what to do next.

### Actor node

An actor node performs actions. It can also have a sensor-like feedback channel, but that feedback should be tuned for extreme sensations rather than every small surface detail. Think of signals like impact, heat, pain, stall, or a failed action attempt.

## Current files

- `spatial_memory_system.py` contains the Torch memory field and local update network.
- `node_roles.py` sketches the base, sensor, reflex, decision, and actor roles around the shared memory core.
- `tokenizer.py` is now a placement helper. Its primary path maps raw numeric streams into scanner-window coordinates. Its byte-level text path is only a debugging convenience.
- `scanner_environment.py` is parked for now. It may be useful later for deterministic movement/path experiments, but it is not the center of the design.
- `demo.py` runs a simple single-process sketch of the four node roles sharing one memory core.
- `desktop_sensor_probe.py` is a standalone raw-number probe for desktop experiments. On Windows 10 it tries PowerShell performance counters first, then falls back to simple process/load values if hardware counters are not exposed.
- `data_logger.py` is a small SQLite logger for viability runs: raw samples, node messages, and memory-step observations.
- `../docs/viability_logging_plan.md` outlines the first database schema and viability questions.

## Raw sensor placement rule

Within a node window, incoming numeric samples fill `x` first, then `y`, then `z`:

```text
origin + (0, 0, 0)
origin + (1, 0, 0)
...
origin + (9, 0, 0)
origin + (0, 1, 0)
```

For a 10x10x10 active window, one local frame can hold up to 1,000 raw numeric samples before the next frame/origin is needed.

## Setup

Install the neural/runtime dependency when you want to run the Torch demo:

```bash
python -m pip install -r requirements.txt
```

The tokenizer and parked scanner-environment tests use only the Python standard library.

## Run the demo

```bash
cd spatial_memory_proto
python demo.py
```

## Probe desktop raw numbers

This is not wired into the model yet. It is only a way to see whether the current desktop exposes constantly changing raw numbers we can map into a local sensor frame.

```bash
cd spatial_memory_proto
python desktop_sensor_probe.py --samples 5 --delay 1
```

On Windows 10, the probe tries CPU, memory, disk, queue-length, temperature, and fan counters through PowerShell/WMI. Temperature and fan readings are often hidden by hardware drivers, so missing values are okay.

## Database logging plan

Start with SQLite so the prototype can log data on a desktop without running a separate database server. The first logger records:

- run metadata,
- raw sensor samples,
- node messages,
- memory-step observations.

See `docs/viability_logging_plan.md` for the schema, first queries, and what we are intentionally not building yet.

## Run tests

From the repository root, run the single test runner file:

```bash
python run_tests.py
```

That file discovers and runs every `test_*.py` file inside the categorized `tests/` folder tree. It also saves a timestamped `.txt` copy of the console output in the `test results/` folder, with a clear pass/fail header at the top.

Current test folders:

- `tests/ai/` for AI/node-role behavior.
- `tests/data_logging/` for SQLite viability logging.
- `tests/data_types/` for value/type conversion assumptions.
- `tests/gpu/` for basic GPU data movement smoke tests.
- `tests/sensors/` for raw sensor/tokenizer placement.
- `tests/spatial_memory/` for scanner and memory-field behavior.
