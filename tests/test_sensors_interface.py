import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sensors.interfaces import (
    DefaultSensorReader,
    FallbackSensorReader,
    RawValueProjector,
    ScannerEnvironment,
    ScannerNavigator,
    SensorReader,
    SensorReading,
    SensorValueProjector,
    WindowsSensorReader,
)


class SensorsInterfaceTest(unittest.TestCase):
    def test_concrete_classes_satisfy_sensor_protocols(self):
        # This is what I expect to happen, DefaultSensorReader() should be an instance of SensorReader.
        self.assertIsInstance(DefaultSensorReader(), SensorReader)
        # This is what I expect to happen, FallbackSensorReader() should be an instance of SensorReader.
        self.assertIsInstance(FallbackSensorReader(), SensorReader)
        # This is what I expect to happen, WindowsSensorReader() should be an instance of SensorReader.
        self.assertIsInstance(WindowsSensorReader(), SensorReader)
        # This is what I expect to happen, SensorValueProjector() should be an instance of RawValueProjector.
        self.assertIsInstance(SensorValueProjector(), RawValueProjector)
        # This is what I expect to happen, ScannerEnvironment() should be an instance of ScannerNavigator.
        self.assertIsInstance(ScannerEnvironment(), ScannerNavigator)

    def test_projector_accesses_values_through_interface_method(self):
        projector: RawValueProjector = SensorValueProjector()
        readings = [SensorReading("cpu", 12.5, "%"), SensorReading("memory", 2048.0, "MB")]

        # This is what I expect to happen, projector.readings_to_spatial_values(readings) should equal [12.5, 2048.0].
        self.assertEqual(projector.readings_to_spatial_values(readings), [12.5, 2048.0])

    def test_windows_reader_is_safe_without_optional_probe(self):
        reader: SensorReader = WindowsSensorReader()

        # This is what I expect to happen, reader.collect_readings() should be an instance of list.
        self.assertIsInstance(reader.collect_readings(), list)


if __name__ == "__main__":
    unittest.main()
