import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(ROOT))

from data_logger import DataLogger, RawSample
from node_roles import NodeConfig
from tentacles.spatial_memory_system import LocalUpdateNet, SpatialMemorySystem
from tentacles.scanner_environment import ScannerConfig, ScannerEnvironment
from sensors.interfaces import SensorReading
from tentacles.tokenizer import ScanFrame, SensorFrame, SpatialTokenizer


class StructuralDataTypesTest(unittest.TestCase):
    def assert_coordinate_tuple(self, value):
        self.assertIsInstance(value, tuple)
        self.assertEqual(len(value), 3)
        self.assertTrue(all(isinstance(axis_value, int) for axis_value in value))

    def test_sensor_reading_uses_expected_primitive_field_types(self):
        reading = SensorReading(name="cpu", value=12.5, unit="%")

        self.assertIsInstance(reading.name, str)
        self.assertIsInstance(reading.value, float)
        self.assertIsInstance(reading.unit, str)

    def test_scanner_config_and_environment_use_coordinate_tuples(self):
        config = ScannerConfig(
            field_size=(20, 30, 40),
            window_size=(5, 6, 7),
            stride=(1, 2, 3),
        )
        environment = ScannerEnvironment(config=config, position=(3, 4, 5))

        self.assert_coordinate_tuple(config.field_size)
        self.assert_coordinate_tuple(config.window_size)
        self.assert_coordinate_tuple(config.stride)
        self.assert_coordinate_tuple(config.max_origin)
        self.assert_coordinate_tuple(environment.position)
        self.assertIsInstance(environment.visited, list)
        self.assertTrue(all(isinstance(point, tuple) for point in environment.visited))

    def test_tokenizer_frames_use_tuple_numeric_payloads(self):
        tokenizer = SpatialTokenizer(window_size=(2, 1, 1), add_eos=True)

        sensor_frame = tokenizer.raw_values_to_frames([0, 255], origins=[(10, 20, 30)])[0]
        scan_frame = tokenizer.encode_to_frames("A", origins=[(0, 0, 0)])[0]

        self.assertIsInstance(sensor_frame, SensorFrame)
        self.assert_coordinate_tuple(sensor_frame.origin)
        self.assert_coordinate_tuple(sensor_frame.window_size)
        self.assertIsInstance(sensor_frame.values, tuple)
        self.assertTrue(all(isinstance(value, float) for value in sensor_frame.values))
        self.assertIsInstance(sensor_frame.coordinates, tuple)
        self.assertTrue(all(isinstance(coord, tuple) for coord in sensor_frame.coordinates))

        self.assertIsInstance(scan_frame, ScanFrame)
        self.assert_coordinate_tuple(scan_frame.origin)
        self.assert_coordinate_tuple(scan_frame.window_size)
        self.assertIsInstance(scan_frame.token_ids, tuple)
        self.assertTrue(all(isinstance(token_id, int) for token_id in scan_frame.token_ids))
        self.assertIsInstance(scan_frame.coordinates, tuple)
        self.assertTrue(all(isinstance(coord, tuple) for coord in scan_frame.coordinates))

    def test_logger_data_types_use_paths_connections_and_raw_samples(self):
        sample = RawSample(source="temperature", value=22.25, unit="C")

        self.assertIsInstance(sample.source, str)
        self.assertIsInstance(sample.value, float)
        self.assertIsInstance(sample.unit, str)

        with tempfile.TemporaryDirectory() as temp_dir:
            db_file = Path(temp_dir) / "viability.sqlite"
            logger = DataLogger(str(db_file))
            try:
                self.assertIsInstance(logger.db_path, Path)
                self.assertIsInstance(logger.connection, sqlite3.Connection)
                self.assertIs(logger.connection.row_factory, sqlite3.Row)
            finally:
                logger.close()

    def test_node_config_and_spatial_memory_system_expose_expected_types(self):
        config = NodeConfig(
            node_id="sensor-1",
            role="sensor",
            channels=2,
            field_size=(4, 4, 4),
            window_size=(2, 2, 2),
            learning_rate=0.001,
        )
        memory = SpatialMemorySystem(
            channels=config.channels,
            field_size=config.field_size,
            window_size=config.window_size,
            movement_mode="static",
        )

        self.assertIsInstance(config.node_id, str)
        self.assertIsInstance(config.role, str)
        self.assertIsInstance(config.channels, int)
        self.assert_coordinate_tuple(config.field_size)
        self.assert_coordinate_tuple(config.window_size)
        self.assertIsInstance(config.learning_rate, float)

        self.assertIsInstance(memory.channels, int)
        self.assert_coordinate_tuple(memory.field_size)
        self.assert_coordinate_tuple(memory.window_size)
        self.assertIsInstance(memory.movement_mode, str)
        self.assertIsInstance(memory.memory_field, torch.nn.Parameter)
        self.assertEqual(tuple(memory.memory_field.shape), (2, 4, 4, 4))
        self.assertIsInstance(memory.update_net, LocalUpdateNet)


if __name__ == "__main__":
    unittest.main()
