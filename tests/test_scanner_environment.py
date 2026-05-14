import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sensors.interfaces import ScannerConfig, ScannerEnvironment


class ScannerEnvironmentTest(unittest.TestCase):
    def test_raster_scan_covers_100_cube_with_10_cube_scanner(self):
        env = ScannerEnvironment(ScannerConfig(field_size=(100, 100, 100), window_size=(10, 10, 10), stride=(10, 10, 10)))

        origins = env.raster_scan()

        self.assertEqual(len(origins), 1000)
        self.assertEqual(origins[0], (0, 0, 0))
        self.assertIn((90, 90, 90), origins)

    def test_path_to_clamps_goal_and_moves_axis_aligned(self):
        env = ScannerEnvironment(position=(0, 0, 0))

        path = env.path_to((200, 20, 0), step=(10, 10, 10))
        final_position = env.follow(path)

        self.assertEqual(final_position, (90, 20, 0))
        self.assertEqual(path[-1], (90, 20, 0))
        self.assertEqual(len(path), 11)

    def test_move_clamps_negative_positions(self):
        env = ScannerEnvironment(position=(10, 10, 10))

        position = env.move((-30, -5, 0))

        self.assertEqual(position, (0, 5, 10))


if __name__ == "__main__":
    unittest.main()
