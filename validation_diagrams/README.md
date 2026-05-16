# Validation diagrams

This folder is for exploratory pandas/matplotlib validation output, not for the
core sensor, node-role, or spatial-memory runtime modules.

The initial sensor diagram flow treats each scanner kernel movement as the
x-axis step. It intentionally does not use wall-clock time as the plotting axis:
raw sensor values are collected once, projected into scanner windows, and then
shown against the kernel step order used to walk the field.

Generated CSV and image files are written to `validation_diagrams/results/`,
which is ignored except for its `.gitignore` placeholder.
