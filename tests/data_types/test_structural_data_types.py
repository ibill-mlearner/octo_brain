import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(ROOT))

from data_logging import DataLogger, RawSample
from node_roles import NodeConfig
from tentacles.spatial_memory_system import LocalUpdateNet, SpatialMemorySystem
from tentacles.scanner_environment import ScannerConfig, ScannerEnvironment
from sensors.interfaces import SensorReading
from tentacles.tokenizer import ScanFrame, SensorFrame, SpatialTokenizer


class StructuralDataTypesTest(unittest.TestCase):
    def assert_coordinate_tuple(self, value):
        # This is what I expect to happen, value should be an instance of tuple.
        self.assertIsInstance(value, tuple)
        # This is what I expect to happen, len(value) should equal 3.
        self.assertEqual(len(value), 3)
        # This is what I expect to happen, all(isinstance(axis_value, int) for axis_value in value) should evaluate as true.
        self.assertTrue(all(isinstance(axis_value, int) for axis_value in value))

    def test_sensor_reading_uses_expected_primitive_field_types(self):
        reading = SensorReading(name="cpu", value=12.5, unit="%")

        # This is what I expect to happen, reading.name should be an instance of str.
        self.assertIsInstance(reading.name, str)
        # This is what I expect to happen, reading.value should be an instance of float.
        self.assertIsInstance(reading.value, float)
        # This is what I expect to happen, reading.unit should be an instance of str.
        self.assertIsInstance(reading.unit, str)

    def test_scanner_config_and_environment_use_coordinate_tuples(self):
        config = ScannerConfig(
            field_size=(20, 30, 40),
            window_size=(5, 6, 7),
            stride=(1, 2, 3),
        )
        environment = ScannerEnvironment(config=config, position=(3, 4, 5))

        # This is what I expect to happen, config.field_size should have the project coordinate tuple shape.
        self.assert_coordinate_tuple(config.field_size)
        # This is what I expect to happen, config.window_size should have the project coordinate tuple shape.
        self.assert_coordinate_tuple(config.window_size)
        # This is what I expect to happen, config.stride should have the project coordinate tuple shape.
        self.assert_coordinate_tuple(config.stride)
        # This is what I expect to happen, config.max_origin should have the project coordinate tuple shape.
        self.assert_coordinate_tuple(config.max_origin)
        # This is what I expect to happen, environment.position should have the project coordinate tuple shape.
        self.assert_coordinate_tuple(environment.position)
        # This is what I expect to happen, environment.visited should be an instance of list.
        self.assertIsInstance(environment.visited, list)
        # This is what I expect to happen, all(isinstance(point, tuple) for point in environment.visited) should evaluate as true.
        self.assertTrue(all(isinstance(point, tuple) for point in environment.visited))

    def test_tokenizer_frames_use_tuple_numeric_payloads(self):
        tokenizer = SpatialTokenizer(window_size=(2, 1, 1), add_eos=True)

        sensor_frame = tokenizer.raw_values_to_frames([0, 255], origins=[(10, 20, 30)])[0]
        scan_frame = tokenizer.encode_to_frames("A", origins=[(0, 0, 0)])[0]

        # This is what I expect to happen, sensor_frame should be an instance of SensorFrame.
        self.assertIsInstance(sensor_frame, SensorFrame)
        # This is what I expect to happen, sensor_frame.origin should have the project coordinate tuple shape.
        self.assert_coordinate_tuple(sensor_frame.origin)
        # This is what I expect to happen, sensor_frame.window_size should have the project coordinate tuple shape.
        self.assert_coordinate_tuple(sensor_frame.window_size)
        # This is what I expect to happen, sensor_frame.values should be an instance of tuple.
        self.assertIsInstance(sensor_frame.values, tuple)
        # This is what I expect to happen, all(isinstance(value, float) for value in sensor_frame.values) should evaluate as true.
        self.assertTrue(all(isinstance(value, float) for value in sensor_frame.values))
        # This is what I expect to happen, sensor_frame.coordinates should be an instance of tuple.
        self.assertIsInstance(sensor_frame.coordinates, tuple)
        # This is what I expect to happen, all(isinstance(coord, tuple) for coord in sensor_frame.coordinates) should evaluate as true.
        self.assertTrue(all(isinstance(coord, tuple) for coord in sensor_frame.coordinates))

        # This is what I expect to happen, scan_frame should be an instance of ScanFrame.
        self.assertIsInstance(scan_frame, ScanFrame)
        # This is what I expect to happen, scan_frame.origin should have the project coordinate tuple shape.
        self.assert_coordinate_tuple(scan_frame.origin)
        # This is what I expect to happen, scan_frame.window_size should have the project coordinate tuple shape.
        self.assert_coordinate_tuple(scan_frame.window_size)
        # This is what I expect to happen, scan_frame.token_ids should be an instance of tuple.
        self.assertIsInstance(scan_frame.token_ids, tuple)
        # This is what I expect to happen, all(isinstance(token_id, int) for token_id in scan_frame.token_ids) should evaluate as true.
        self.assertTrue(all(isinstance(token_id, int) for token_id in scan_frame.token_ids))
        # This is what I expect to happen, scan_frame.coordinates should be an instance of tuple.
        self.assertIsInstance(scan_frame.coordinates, tuple)
        # This is what I expect to happen, all(isinstance(coord, tuple) for coord in scan_frame.coordinates) should evaluate as true.
        self.assertTrue(all(isinstance(coord, tuple) for coord in scan_frame.coordinates))

    def test_logger_data_types_use_paths_connections_and_raw_samples(self):
        sample = RawSample(source="temperature", value=22.25, unit="C")

        # This is what I expect to happen, sample.source should be an instance of str.
        self.assertIsInstance(sample.source, str)
        # This is what I expect to happen, sample.value should be an instance of float.
        self.assertIsInstance(sample.value, float)
        # This is what I expect to happen, sample.unit should be an instance of str.
        self.assertIsInstance(sample.unit, str)

        with tempfile.TemporaryDirectory() as temp_dir:
            db_file = Path(temp_dir) / "viability.sqlite"
            logger = DataLogger(str(db_file))
            try:
                # This is what I expect to happen, logger.db_path should be an instance of Path.
                self.assertIsInstance(logger.db_path, Path)
                # This is what I expect to happen, logger.connection should be an instance of sqlite3.Connection.
                self.assertIsInstance(logger.connection, sqlite3.Connection)
                # This is what I expect to happen, logger.connection.row_factory should be the same object as sqlite3.Row.
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

        # This is what I expect to happen, config.node_id should be an instance of str.
        self.assertIsInstance(config.node_id, str)
        # This is what I expect to happen, config.role should be an instance of str.
        self.assertIsInstance(config.role, str)
        # This is what I expect to happen, config.channels should be an instance of int.
        self.assertIsInstance(config.channels, int)
        # This is what I expect to happen, config.field_size should have the project coordinate tuple shape.
        self.assert_coordinate_tuple(config.field_size)
        # This is what I expect to happen, config.window_size should have the project coordinate tuple shape.
        self.assert_coordinate_tuple(config.window_size)
        # This is what I expect to happen, config.learning_rate should be an instance of float.
        self.assertIsInstance(config.learning_rate, float)

        # This is what I expect to happen, memory.channels should be an instance of int.
        self.assertIsInstance(memory.channels, int)
        # This is what I expect to happen, memory.field_size should have the project coordinate tuple shape.
        self.assert_coordinate_tuple(memory.field_size)
        # This is what I expect to happen, memory.window_size should have the project coordinate tuple shape.
        self.assert_coordinate_tuple(memory.window_size)
        # This is what I expect to happen, memory.movement_mode should be an instance of str.
        self.assertIsInstance(memory.movement_mode, str)
        # This is what I expect to happen, memory.memory_field should be an instance of torch.nn.Parameter.
        self.assertIsInstance(memory.memory_field, torch.nn.Parameter)
        # This is what I expect to happen, tuple(memory.memory_field.shape) should equal (2, 4, 4, 4).
        self.assertEqual(tuple(memory.memory_field.shape), (2, 4, 4, 4))
        # This is what I expect to happen, memory.update_net should be an instance of LocalUpdateNet.
        self.assertIsInstance(memory.update_net, LocalUpdateNet)


if __name__ == "__main__":
    unittest.main()
