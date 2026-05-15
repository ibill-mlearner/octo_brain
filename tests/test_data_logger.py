import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_logging import DataLogger, RawSample


class DataLoggerTest(unittest.TestCase):
    def test_logs_viability_run_records(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "viability.sqlite3"
            with DataLogger(db_path) as logger:
                run_id = logger.create_run("unit-test", metadata={"purpose": "viability"})

                logger.log_raw_samples(
                    run_id,
                    step=0,
                    samples=[RawSample("cpu", 12.5, "%"), RawSample("memory", 2048.0, "MB")],
                )
                logger.log_node_message(
                    run_id,
                    step=0,
                    message={
                        "node_id": "sensor-1",
                        "role": "sensor",
                        "state": 0.25,
                        "error": 0.1,
                        "confidence": 0.75,
                        "urgency": 0.2,
                    },
                    payload={"source": "unit-test"},
                )
                logger.log_memory_step(
                    run_id,
                    step=0,
                    position=(1, 2, 3),
                    error=0.1,
                    reflex_triggered=True,
                    write_back=True,
                )

                # This is what I expect to happen, logger.count_rows("runs") should equal 1.
                self.assertEqual(logger.count_rows("runs"), 1)
                # This is what I expect to happen, logger.count_rows("raw_sensor_samples") should equal 2.
                self.assertEqual(logger.count_rows("raw_sensor_samples"), 2)
                # This is what I expect to happen, logger.count_rows("node_messages") should equal 1.
                self.assertEqual(logger.count_rows("node_messages"), 1)
                # This is what I expect to happen, logger.count_rows("memory_steps") should equal 1.
                self.assertEqual(logger.count_rows("memory_steps"), 1)

    def test_memory_step_requires_xyz_position(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "viability.sqlite3"
            with DataLogger(db_path) as logger:
                run_id = logger.create_run("unit-test")

                # This is what I expect to happen, the next operation should raise ValueError.
                with self.assertRaises(ValueError):
                    logger.log_memory_step(run_id, step=0, position=(1, 2))


if __name__ == "__main__":
    unittest.main()
