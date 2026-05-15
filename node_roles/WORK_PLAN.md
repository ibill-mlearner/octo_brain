# Node Roles Split Work Plan

This document is a working plan for untangling the current `node_roles` package. The goal is to separate the large persistent memory scope, the smaller moving actors that operate inside that scope, and the external actions that affect the outside environment.

The current files are useful prototypes, but they mix several responsibilities in one package. This plan keeps the changes small and inspectable while moving toward clearer modules or packages.

## Design target

Keep these concepts separate:

1. **Static memory scope**
   - The large `100 x 100 x 100` spatial parameter field.
   - The durable learned behavior and broad processing substrate.
   - The thing local actors move through and modify.

2. **Memory actors**
   - Smaller moving windows such as the current `10 x 10 x 10` local process.
   - Internal actors that read a patch, carry active state, write local updates, and move within the larger scope.
   - Not the same thing as external actions.

3. **External actions**
   - Outputs that affect something outside the AI.
   - Examples: actuator commands, device movement, environment writes, or any outward-facing control signal.
   - Should be kept distinct from an internal actor moving through memory.

4. **Streaming inputs**
   - Continuous numerical sensor values.
   - Inputs should be routed into active state or local memory patches without assuming an image/text preprocessing pipeline.

5. **Coordination and messages**
   - Lightweight messages between internal pieces.
   - Error, confidence, urgency, movement, and output proposals should be explicit enough to route without tightly coupling every module.

## Current responsibility map

Use this map before moving files so each responsibility has one intended home.

| Current file | Current responsibility | Future home to consider |
| --- | --- | --- |
| `base_node.py` | Moving-window state container and shared hooks | Memory actor base module |
| `sensor_node.py` | Numeric input ingestion and local prediction | Streaming input or sensor actor module |
| `reflex_node.py` | Error-to-urgency path | Reflex/urgency module |
| `decision_node.py` | Movement/action proposal | Decision or routing module |
| `actor_node.py` | Internal actor state plus action execution | Split between memory actor and external action adapter |
| `actions.py` | Action execution helper | External actions package/module |
| `agent_controller.py` | Combined older controller with training-shaped logic | Legacy/prototype area until replaced |
| `server.py` | Role registry/factory | Coordination or composition module |
| `node_config.py` | Shared configuration | Shared config module |

## Phase 1: Name the layers before moving code

Before creating packages, decide on the vocabulary to avoid repeating the current ambiguity.

- Choose a name for the large static parameter scope.
  - Candidate names: `memory_scope`, `static_memory`, `parameter_field`, `memory_node`.
- Choose a name for the smaller moving window.
  - Candidate names: `memory_actor`, `window_actor`, `local_actor`, `patch_actor`.
- Reserve `action` for external effects outside the AI.
- Decide whether `node_roles` remains the public package name or becomes a compatibility layer over clearer packages.

Deliverable:

- Update documentation with the selected names before any large file moves.

## Phase 2: Split internal actors from external actions

The first concrete split should separate internal memory actors from outward-facing actions.

Steps:

1. Create a home for internal moving-window actors.
   - Move or copy the `BaseNode` concept there once names are settled.
   - Keep `position`, `velocity`, `active_state`, and patch access together.
2. Create a home for external actions.
   - Move `Actions` and `ActionResult` concepts there.
   - Keep actuator/output semantics out of the internal actor base.
3. Update `ActorNode` naming or structure.
   - Make clear whether it is an internal actor on memory, an external action adapter, or a bridge between the two.

Deliverable:

- A small module boundary where internal memory movement and external environment effects are no longer described as the same thing.

## Phase 3: Separate streaming inputs from decision/reflex behavior

Once actor/action boundaries are clear, separate continuous numeric input flow from control logic.

Steps:

1. Give numeric sensor ingestion a clear module.
   - Preserve the idea that sensors stream numerical values directly.
   - Keep raw-value-to-active-state mapping inspectable.
2. Keep reflex behavior separate from decision behavior.
   - Reflex should remain the immediate urgency path.
   - Decision should remain the slower proposal/routing path.
3. Make the message fields explicit.
   - Error, confidence, urgency, movement proposals, and action proposals should have clear names.

Deliverable:

- Sensor ingestion, reflex urgency, and decision routing can change independently.

## Phase 4: Isolate legacy training-shaped code

`AgentController` currently combines prediction, decision, reflex override, optimization, and memory updates. That makes it useful as a prototype reference, but risky as the organizing center.

Steps:

1. Move or mark `AgentController` as legacy/prototype once replacement pieces exist.
2. Extract any still-useful message or loop ideas into the new modules.
3. Avoid letting optimizer-based training flow define the package boundaries.

Deliverable:

- New code does not need to import the combined controller to use the clearer memory actor/action/sensor pieces.

## Phase 5: Add compatibility shims only after boundaries are stable

If public imports need to remain stable, keep `node_roles/__init__.py` or old module names as thin compatibility shims.

Steps:

1. Re-export moved classes from old paths temporarily.
2. Add comments explaining which new module owns the real implementation.
3. Remove shims only when callers have been updated.

Deliverable:

- Existing demos or exploratory scripts can keep working while the internal layout improves.

## Suggested future package shape

This is only a draft. Rename it as the vocabulary settles.

```text
memory_scope/
    static_memory.py        # large persistent field-facing concepts
    config.py

memory_actors/
    base_actor.py           # moving-window state and patch interaction
    sensor_actor.py         # numeric stream ingestion into local state
    reflex_actor.py         # urgency/error path
    decision_actor.py       # movement/output proposals

actions/
    external_action.py      # outward effects outside the AI
    adapters.py             # actuator/device/environment bridges

coordination/
    messages.py             # shared message objects or dictionaries
    registry.py             # factory/server/composition helpers

legacy/
    agent_controller.py     # older combined training-shaped prototype
```

## Order of operations checklist

Use this checklist for each migration patch:

- Move only one responsibility at a time.
- Keep imports working after each step.
- Avoid broad renames unless the vocabulary has been decided first.
- Do not mix documentation, package moves, and behavioral changes in the same patch if they can be separated.
- Preserve the distinction between persistent memory, visible patches, active state, internal actors, and external actions.
- Note that test execution is reserved for the human project owner when tests would normally be run.
