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
    SpatialFramePlacer,
    SpatialTokenizer,
    WindowsSensorReader,
)


class SensorsInterfaceTest(unittest.TestCase):
    def test_concrete_classes_satisfy_sensor_protocols(self):
        self.assertIsInstance(DefaultSensorReader(), SensorReader)
        self.assertIsInstance(FallbackSensorReader(), SensorReader)
        self.assertIsInstance(WindowsSensorReader(), SensorReader)
        self.assertIsInstance(SensorValueProjector(), RawValueProjector)
        self.assertIsInstance(ScannerEnvironment(), ScannerNavigator)
        self.assertIsInstance(SpatialTokenizer(), SpatialFramePlacer)

    def test_projector_accesses_values_through_interface_method(self):
        projector: RawValueProjector = SensorValueProjector()
        readings = [SensorReading("cpu", 12.5, "%"), SensorReading("memory", 2048.0, "MB")]

        self.assertEqual(projector.readings_to_spatial_values(readings), [12.5, 2048.0])

    def test_windows_reader_is_safe_when_powershell_is_missing(self):
        reader: SensorReader = WindowsSensorReader()

        self.assertIsInstance(reader.collect_readings(), list)


if __name__ == "__main__":
    unittest.main()
