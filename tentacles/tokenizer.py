# Moved out of the sensors package because sensors should stay raw/non-AI; this spatial placement helper belongs with the tentacles package.
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

Coordinate = Tuple[int, int, int]
WindowSize = Tuple[int, int, int]


@dataclass(frozen=True)
class ScanFrame:
    """A debug/text token chunk placed inside one 3D scanner window."""

    origin: Coordinate
    window_size: WindowSize
    token_ids: Tuple[int, ...]
    coordinates: Tuple[Coordinate, ...]


@dataclass(frozen=True)
class SensorFrame:
    """Raw sensor samples placed directly into one 3D scanner window."""

    origin: Coordinate
    window_size: WindowSize
    values: Tuple[float, ...]
    coordinates: Tuple[Coordinate, ...]


class SpatialTokenizer:
    """
    Placement helper for raw sensor streams and optional text debugging.

    The model is not meant to parse camera frames, pressure readings, or other
    sensors into semantic language tokens first. The fast path keeps readings as
    plain numbers, normalizes them into a stable range, and assigns them to cells
    in the active scanner window. Text encode/decode remains here only as a small
    reversible debugging path while the raw numeric path is built out.
    """

    PAD = 0
    EOS = 1
    UNK = 2
    BYTE_OFFSET = 3
    VOCAB_SIZE = BYTE_OFFSET + 256

    def __init__(self, window_size: WindowSize = (10, 10, 10), add_eos: bool = True):
        self.window_size = window_size
        self.add_eos = add_eos
        self.special_tokens = {
            "<pad>": self.PAD,
            "<eos>": self.EOS,
            "<unk>": self.UNK,
        }

    @property
    def window_volume(self) -> int:
        x, y, z = self.window_size
        return x * y * z

    def encode(self, text: str) -> List[int]:
        """Reversible byte-level text path for debug experiments."""
        token_ids = [byte + self.BYTE_OFFSET for byte in text.encode("utf-8")]
        if self.add_eos:
            token_ids.append(self.EOS)
        return token_ids

    def decode(self, token_ids: Iterable[int], stop_at_eos: bool = True) -> str:
        """Decode ids produced by `encode`; ignores padding and unknown ids."""
        data = bytearray()
        for token_id in token_ids:
            if token_id == self.EOS and stop_at_eos:
                break
            if token_id in (self.PAD, self.EOS, self.UNK):
                continue
            if self.BYTE_OFFSET <= token_id < self.VOCAB_SIZE:
                data.append(token_id - self.BYTE_OFFSET)
        return data.decode("utf-8", errors="replace")

    def normalize_raw_values(self, values: Iterable[float], min_value: float = 0.0, max_value: float = 255.0) -> List[float]:
        """Normalize raw sensor numbers to 0..1 without semantic compression."""
        if max_value <= min_value:
            raise ValueError("max_value must be greater than min_value")

        span = max_value - min_value
        normalized = []
        for value in values:
            clipped = min(max(float(value), min_value), max_value)
            normalized.append((clipped - min_value) / span)
        return normalized

    def chunk(self, values: Sequence[float | int]) -> List[Tuple[float | int, ...]]:
        if self.window_volume <= 0:
            raise ValueError("window volume must be positive")
        return [tuple(values[i : i + self.window_volume]) for i in range(0, len(values), self.window_volume)]

    def local_coordinate(self, local_index: int) -> Coordinate:
        if local_index < 0 or local_index >= self.window_volume:
            raise IndexError("local_index is outside the scanner window")

        wx, wy, _ = self.window_size
        x = local_index % wx
        y = (local_index // wx) % wy
        z = local_index // (wx * wy)
        return (x, y, z)

    def coordinates_for_count(self, origin: Coordinate, count: int) -> Tuple[Coordinate, ...]:
        if count > self.window_volume:
            raise ValueError("count exceeds scanner window volume")

        ox, oy, oz = origin
        coords = []
        for local_index in range(count):
            lx, ly, lz = self.local_coordinate(local_index)
            coords.append((ox + lx, oy + ly, oz + lz))
        return tuple(coords)

    def token_coordinates(self, origin: Coordinate, count: int) -> Tuple[Coordinate, ...]:
        """Backward-compatible name for text/debug token coordinate placement."""
        return self.coordinates_for_count(origin, count)

    def raw_values_to_frames(
        self,
        values: Sequence[float],
        origins: Sequence[Coordinate],
        min_value: float = 0.0,
        max_value: float = 255.0,
    ) -> List[SensorFrame]:
        """Place normalized raw sensor values into supplied scanner origins."""
        normalized_chunks = self.chunk(self.normalize_raw_values(values, min_value=min_value, max_value=max_value))
        if len(origins) < len(normalized_chunks):
            raise ValueError("not enough scanner origins supplied for raw sensor values")

        frames = []
        for origin, value_chunk in zip(origins, normalized_chunks):
            values_tuple = tuple(float(value) for value in value_chunk)
            frames.append(
                SensorFrame(
                    origin=origin,
                    window_size=self.window_size,
                    values=values_tuple,
                    coordinates=self.coordinates_for_count(origin, len(values_tuple)),
                )
            )
        return frames

    def encode_to_frames(self, text: str, origins: Sequence[Coordinate]) -> List[ScanFrame]:
        """Encode debug text and place chunks into the supplied scanner origins."""
        token_chunks = self.chunk(self.encode(text))
        if len(origins) < len(token_chunks):
            raise ValueError("not enough scanner origins supplied for tokenized text")

        frames = []
        for origin, token_chunk in zip(origins, token_chunks):
            token_ids = tuple(int(token_id) for token_id in token_chunk)
            frames.append(
                ScanFrame(
                    origin=origin,
                    window_size=self.window_size,
                    token_ids=token_ids,
                    coordinates=self.coordinates_for_count(origin, len(token_ids)),
                )
            )
        return frames
