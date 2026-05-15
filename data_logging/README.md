# Data logging

`data_logging` is only for logging raw input data.

In the current prototype, raw input data means sensor readings: CPU, process,
disk, load, and other machine/runtime values that can later be consumed by the
spatial-memory layers. This package should stay focused on recording those raw
sensor samples and the run metadata needed to interpret them.

This package should **not** log moving-window state, memory positions, node role
messages, reflex behavior, prediction-error handling, or write-back decisions.
Those concepts belong to the spatial-memory and node-role layers, where the
raw sensor inputs are interpreted after collection.
