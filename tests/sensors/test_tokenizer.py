import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tentacles.tokenizer import SpatialTokenizer


class SpatialTokenizerTest(unittest.TestCase):
    def test_raw_sensor_values_are_normalized_without_semantic_tokens(self):
        tokenizer = SpatialTokenizer(add_eos=True)

        values = tokenizer.normalize_raw_values([-10, 0, 127.5, 255, 300])

        self.assertEqual(values, [0.0, 0.0, 0.5, 1.0, 1.0])

    def test_raw_values_are_placed_into_spatial_frames(self):
        tokenizer = SpatialTokenizer(window_size=(2, 2, 1), add_eos=False)

        frames = tokenizer.raw_values_to_frames([0, 127.5, 255, 64, 32], origins=[(0, 0, 0), (10, 0, 0)])

        self.assertEqual(len(frames), 2)
        self.assertEqual(frames[0].values, (0.0, 0.5, 1.0, 64 / 255))
        self.assertEqual(frames[0].coordinates, ((0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)))
        self.assertEqual(frames[1].values, (32 / 255,))
        self.assertEqual(frames[1].coordinates, ((10, 0, 0),))

    def test_coordinates_fill_x_then_y_then_z(self):
        tokenizer = SpatialTokenizer(window_size=(10, 10, 10), add_eos=False)

        coords = tokenizer.coordinates_for_count((20, 30, 40), 12)

        self.assertEqual(coords[0], (20, 30, 40))
        self.assertEqual(coords[9], (29, 30, 40))
        self.assertEqual(coords[10], (20, 31, 40))
        self.assertEqual(coords[11], (21, 31, 40))

    def test_raw_values_to_frames_requires_enough_origins(self):
        tokenizer = SpatialTokenizer(window_size=(2, 2, 1), add_eos=False)

        with self.assertRaises(ValueError):
            tokenizer.raw_values_to_frames([0, 1, 2, 3, 4], origins=[(0, 0, 0)])

    def test_text_round_trip_remains_for_debugging(self):
        tokenizer = SpatialTokenizer(add_eos=True)
        text = "scanner memory: hello π"

        token_ids = tokenizer.encode(text)

        self.assertEqual(token_ids[-1], SpatialTokenizer.EOS)
        self.assertEqual(tokenizer.decode(token_ids), text)


class DesktopSensorProbeTest(unittest.TestCase):
    def test_probe_readings_can_be_turned_into_raw_values(self):
        from sensors.interfaces import SensorReading, readings_to_spatial_values

        readings = [SensorReading("cpu", 12.5, "%"), SensorReading("memory", 2048.0, "MB")]

        self.assertEqual(readings_to_spatial_values(readings), [12.5, 2048.0])


if __name__ == "__main__":
    unittest.main()
