<!-- AI agents: prefer AGENTS.machine.json for the compact machine-readable version of these instructions; this Markdown file is the human-readable companion. -->

# Agent Instructions

These instructions apply to the entire repository.

## Test execution

- AI coding agents must not run the project's tests, test runner, or test-like commands.
- This includes, but is not limited to, `python run_tests.py`, `pytest`, `unittest`, and direct execution of files under `tests/`.
- Only the human project owner should run tests for this repository.
- When making code changes, agents should note that tests were intentionally not run because this repository reserves test execution for a human.

## Future-agent workflow notes

- Read `CODING_PRACTICES.md` before shaping Python edits. The owner prefers vertical, list-like function signatures when signatures grow beyond a few simple arguments.
- Treat `docs/spatial_memory_engineering_explanation.md` as the conceptual map for the project. The code is an early spatial-memory/node-role prototype, so preserve the distinction between persistent memory, local patches, active state, movement, prediction error, reflex behavior, and node messages.
- Be careful with behavioral changes in `spatial_memory_system.py`. Existing comments document prior reverted stability ideas; do not reintroduce clamps, bounds, scaling knobs, or recurrent-update changes unless the owner explicitly asks for that direction.
- Prefer small, inspectable patches. This repository contains several exploratory modules and duplicated/legacy playground files, so avoid broad cleanup or renaming unless specifically requested.
- Do not edit generated artifacts or local run outputs such as `__pycache__/`, `*.pyc`, or files under `test results/` except for intentional repository placeholder files.
- If a change touches sensor scanning, data logging, or node roles, first identify whether the canonical file is at the repository root, under `sensors/`, or under `node_roles/`; there are similarly named modules used for different prototype layers.
- When tests would normally be appropriate, leave a clear note in the final response and PR body that testing is reserved for the human project owner.
