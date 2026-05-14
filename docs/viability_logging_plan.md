# Viability Logging Plan

The next useful milestone is not a smarter model yet. It is a repeatable way to record what the prototype is doing so we can inspect whether the spatial-memory idea is viable.

## Goal

Create a small local database log that can answer basic questions:

- Did raw sensor values arrive continuously?
- Which node saw those values?
- What did each node report as error, confidence, urgency, or feedback?
- Which memory position/window was active at each step?
- Did the system rewrite memory, trigger a reflex, or choose an actor action?
- Can we compare one run against another run later?

## First database target

Use SQLite first.

Reasons:

- It is built into Python, so no extra server is needed.
- It works on Windows desktops.
- It is enough for early viability testing.
- We can replace or mirror it later with DuckDB, Postgres, Parquet, or a time-series database if the logs get large.

## Minimum viable schema

### `runs`

One row per prototype execution.

Fields:

- `run_id`
- `started_at`
- `label`
- `metadata_json`

### `raw_sensor_samples`

Raw numeric values from sensors or desktop probes.

Fields:

- `sample_id`
- `run_id`
- `step`
- `source`
- `sample_index`
- `value`
- `unit`
- `captured_at`

### `node_messages`

Messages emitted by base/sensor/reflex/decision/actor nodes.

Fields:

- `message_id`
- `run_id`
- `step`
- `node_id`
- `role`
- `state`
- `error`
- `confidence`
- `urgency`
- `payload_json`
- `captured_at`

### `memory_steps`

Spatial memory movement/update observations.

Fields:

- `memory_step_id`
- `run_id`
- `step`
- `position_x`
- `position_y`
- `position_z`
- `error`
- `reflex_triggered`
- `write_back`
- `payload_json`
- `captured_at`

## Early viability loop

1. Start a run row.
2. Probe desktop raw numbers, or use synthetic numbers if no hardware counters are exposed.
3. Log the raw numeric samples.
4. Feed those numbers into a sensor node.
5. Log the sensor node message.
6. Step the memory once.
7. Log the active memory position and write-back/reflex/error values.
8. Repeat for a small number of steps.
9. Inspect the database with simple SQL queries.

## Useful first queries

```sql
select source, count(*) as samples, min(value), max(value), avg(value)
from raw_sensor_samples
group by source;
```

```sql
select role, count(*) as messages, avg(error), avg(urgency)
from node_messages
group by role;
```

```sql
select step, position_x, position_y, position_z, error, reflex_triggered, write_back
from memory_steps
order by step;
```

## What we are not doing yet

- No distributed database.
- No vector database.
- No live dashboard.
- No automatic training analysis.
- No long-term compression strategy.

Those can come later. The first target is simply: can we capture enough numbers to see what the prototype is doing?
