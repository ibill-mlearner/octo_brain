# Node Roles Package

The `node_roles` package is the working area for describing how local processes interact with the spatial memory field. The project still wants a large parameter scope for heavy processing. The important difference from a conventional model is that this large scope is not only something queried after a separate training phase; it is also the persistent memory surface that local processes can keep updating while the system runs.

In the current prototype, that large scope is the `100 x 100 x 100` spatial field. Those one million positions are the persistent parameter space where learned behavior can live. Sensor data is expected to stream in continuously as numerical values, and the system should be able to keep processing and updating against that stream instead of first converting everything into a separate high-level representation.

## Core split

There are two concepts that should stay separate while the naming is refined:

- A large static parameter scope: the memory-like field that holds the durable behavior and provides the broad processing substrate.
- A smaller moving actor: the `10 x 10 x 10` local window that travels inside the larger scope, reads a local patch, carries temporary active state, and can change the parameters inside its current window.

This may eventually become two packages or two clearer layers. One layer would describe the static memory node: the large parameter field that can be interacted with. Another layer would describe the actors on that memory: smaller moving windows that operate inside the larger parameter scope.

The word `actor` here means an internal process that acts on the memory field. That is separate from an `action`, which should mean an external effect outside the AI, such as moving a device, changing an actuator, or sending an output to the environment.

## Moving-window loop

The moving actor/window is the mechanism that locally changes the persistent field. It runs around the field like a sliding local process:

- read the local persistent patch;
- combine it with transient active state and incoming numeric signals;
- produce an internal result, movement result, or external action proposal;
- write allowed local changes back into the persistent field;
- move on to another local patch.

There is no separate traditional training cycle implied by this package. Running, adapting, and learning are intended to be part of the same ongoing stream. The large parameter field can still be treated as a stable processing scope, but updates are expected to happen through local actors operating inside that scope rather than through a separate whole-model training pass.

## What `BaseNode` is for

`BaseNode` is currently the shared handle for the moving local actor/window. It should not be treated as the final answer to whether a "node" means the large static memory scope or the smaller actor moving through it. That naming is still open.

For now, `BaseNode` keeps the state needed by the smaller process that operates inside the larger field:

- `config`: the node identifier, role name, channel count, field size, window size, and learning-rate setting.
- `core`: the shared `SpatialMemorySystem`, which contains the larger persistent parameter field.
- `device`: the tensor device inherited from the memory field.
- `position`: where the local window currently sits in the persistent field.
- `velocity`: the recent movement of that window through the field.
- `active_state`: temporary local state with shape `1 x channels x window_x x window_y x window_z`.

The important split is:

- the persistent field is the durable parameter scope;
- the visible patch is the part of that parameter scope currently under the moving actor;
- the active state is temporary working state for the local actor;
- the base node is the current interface that keeps those pieces aligned.

`BaseNode` provides only the common mechanics:

- `sync_from(other)` copies movement and active state from another local process.
- `ingest_raw_values(values)` is a shared hook for feeding numeric sensor-like signals into a role without hard-coding the role type.
- `_write_values_to_active(values)` maps numeric values into the temporary active tensor.
- `to_message(error, confidence, urgency)` turns the current local state into a small coordination message.

New role work should preserve this separation. If a role needs behavior, it should usually add behavior around the moving actor/window rather than blur the distinction between the large memory scope, the local process acting on it, and external actions.

## Current role files

These files are still exploratory. They describe different ways the moving actor/window can be used, not a final ontology of separate agents.

- `SensorNode`: feeds raw numeric readings into the active state and compares the active state with a local memory patch.
- `ReflexNode`: converts error into an immediate trigger and urgency signal.
- `DecisionNode`: uses active state, error, and velocity to propose a rounded movement or action tensor.
- `ActorNode`: represents an internal actor on memory that applies movement/action tensors through `Actions` and reports movement feedback.
- `Actions`: keeps external action execution separate from the internal actor state container.
- `NodeRoleServer`: creates role-shaped moving-window handles from a shared memory core.
- `AgentController`: an older combined controller that still contains more conventional training-shaped code and should not be treated as the final intent.

## Direction for future work

When this package is expanded, keep the central split visible: the large field is the durable parameter scope, and the smaller actor/window is the thing that moves through that scope and changes local parameters. It may be cleaner to separate those concepts into distinct packages or layers as the design settles.
