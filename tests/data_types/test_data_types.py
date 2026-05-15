import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tentacles.tokenizer import SpatialTokenizer


class DataTypesTest(unittest.TestCase):
    def test_raw_sensor_frames_use_float_values_and_integer_coordinates(self):
        tokenizer = SpatialTokenizer(window_size=(2, 2, 1), add_eos=False)

        frame = tokenizer.raw_values_to_frames([0, 128, 255], origins=[(5, 6, 7)])[0]

        # This is what I expect to happen, all(isinstance(value, float) for value in frame.values) should evaluate as true.
        self.assertTrue(all(isinstance(value, float) for value in frame.values))
        # This is what I expect to happen, all(isinstance(axis_value, int) for coord in frame.coordinates for axis_value i... should evaluate as true.
        self.assertTrue(all(isinstance(axis_value, int) for coord in frame.coordinates for axis_value in coord))

    def test_debug_text_tokens_are_integers(self):
        tokenizer = SpatialTokenizer(add_eos=True)

        token_ids = tokenizer.encode("abc")

        # This is what I expect to happen, all(isinstance(token_id, int) for token_id in token_ids) should evaluate as true.
        self.assertTrue(all(isinstance(token_id, int) for token_id in token_ids))


if __name__ == "__main__":
    unittest.main()
