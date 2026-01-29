"""Utility functions for binary I/O, MessagePack serialization, and PNG handling.

This module provides low-level functions for reading and writing binary data,
MessagePack serialization with special handling for KKEx data, and PNG image extraction.
"""

import struct
from typing import Any, BinaryIO

from msgpack import packb, unpackb
from msgpack.fallback import Packer as PurePacker


def load_length(data_stream: BinaryIO, struct_type: str) -> bytes:
    """Read length-prefixed data from a binary stream.

    Args:
        data_stream: Binary stream to read from.
        struct_type: Struct format character for the length field (e.g., 'i', 'b', 'q').

    Returns:
        The data bytes read after the length prefix.
    """
    length = struct.unpack(struct_type, data_stream.read(struct.calcsize(struct_type)))[0]
    return data_stream.read(length)


def load_string(data_stream: BinaryIO) -> bytes:
    """Read a variable-length encoded string from a binary stream.

    Uses 7-bit variable-length encoding where the MSB indicates continuation.

    Args:
        data_stream: Binary stream to read from.

    Returns:
        The string data as bytes.
    """
    length = 0
    i = 0
    while True:
        serial = struct.unpack("B", data_stream.read(struct.calcsize("B")))[0]
        length |= (0b01111111 & serial) << 7 * i
        if serial >> 7 != 1:
            break
        i += 1
    data = data_stream.read(length)
    return data


def load_type(data_stream: BinaryIO, struct_type: str) -> Any:
    """Read a single value of a specific type from a binary stream.

    Args:
        data_stream: Binary stream to read from.
        struct_type: Struct format character for the data type (e.g., 'i', 'f', 'b').

    Returns:
        The unpacked value.
    """
    return struct.unpack(struct_type, data_stream.read(struct.calcsize(struct_type)))[0]


def write_string(data_stream: BinaryIO, value: bytes) -> None:
    """Write a variable-length encoded string to a binary stream.

    Uses 7-bit variable-length encoding where the MSB indicates continuation.

    Args:
        data_stream: Binary stream to write to.
        value: The string data as bytes to write.
    """
    length = len(value)
    parts: list[int] = []
    while True:
        byte = length & 0x7F
        length >>= 7
        if length:
            parts.append(0x80 | byte)
        else:
            parts.append(byte)
            break
    data_stream.write(bytes(parts))
    data_stream.write(value)


def msg_unpack(data: bytes | None) -> Any:
    """Deserialize MessagePack data.

    Args:
        data: MessagePack-encoded bytes, or None.

    Returns:
        The deserialized Python object.
    """
    return unpackb(data, raw=False, strict_map_key=False)


def msg_pack(data: Any) -> tuple[bytes, int]:
    """Serialize data to MessagePack format.

    Args:
        data: Python object to serialize.

    Returns:
        A tuple of (serialized_bytes, length).
    """
    serialized = packb(data, use_single_float=True, use_bin_type=True)
    return serialized, len(serialized)


class KKExPacker(PurePacker):
    """Custom MessagePack packer for KKEx data.

    This packer overrides specific keys to use int32 format (0xd2) instead of
    the default compact integer format. This is required for compatibility
    with the game's MessagePack deserializer.

    Attributes:
        KEYS_TO_OVERRIDE: Set of keys that require int32 format override.
    """

    KEYS_TO_OVERRIDE: set[int | str] = {
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        "AllCharaOverlayTable",
        "BreathingBPM",
        "CurrentCrest",
        "EnableBulge",
        "InmonLevel",
        "LeaveSchoolWeek",
        "MenstruationSchedule",
        "ReferralIndex",
        "ResizeCentroid",
        "ReturnToSchoolWeek",
        "SemenVolume",
        "clothingOffsetVersion",
    }

    def _pack_map_pairs(self, n: int, pairs: Any, nest_limit: int) -> None:
        """Pack map key-value pairs with special handling for override keys.

        Args:
            n: Number of pairs.
            pairs: Iterable of (key, value) tuples.
            nest_limit: Recursion depth limit.
        """
        self._pack_map_header(n)
        for k, v in pairs:
            if k in self.KEYS_TO_OVERRIDE and isinstance(k, int):
                self._buffer.write(b"\xd2" + struct.pack(">i", k))
            else:
                self._pack(k, nest_limit - 1)

            if k in self.KEYS_TO_OVERRIDE and isinstance(v, int):
                self._buffer.write(b"\xd2" + struct.pack(">i", v))
            else:
                self._pack(v, nest_limit - 1)


def msg_pack_kkex(data: Any) -> tuple[bytes, int]:
    """Serialize data to MessagePack format using KKEx-specific packer.

    Args:
        data: Python object to serialize.

    Returns:
        A tuple of (serialized_bytes, length).
    """
    packer = KKExPacker(use_single_float=True, use_bin_type=True)
    serialized = packer.pack(data)
    return serialized, len(serialized)


PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def has_png_magic(data_stream: BinaryIO) -> bool:
    """Check if the data stream starts with PNG magic number.

    Reads the first 8 bytes and restores the stream position.

    Args:
        data_stream: Binary stream to check.

    Returns:
        True if the stream starts with PNG magic number, False otherwise.
    """
    start_pos = data_stream.tell()
    head = data_stream.read(len(PNG_MAGIC))
    data_stream.seek(start_pos)
    return head == PNG_MAGIC


def get_png_length(png_data: bytes, orig: int = 0) -> int:
    """Calculate the length of a PNG image in a byte buffer.

    Args:
        png_data: Byte buffer containing PNG data.
        orig: Starting offset in the buffer.

    Returns:
        The length of the PNG image from the start offset.

    Raises:
        AssertionError: If the data does not start with a valid PNG signature.
    """
    idx = orig
    assert png_data[idx : idx + 8] == b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a"

    idx += 8
    while True:
        chunk_len = struct.unpack(">I", png_data[idx : idx + 4])[0]
        chunk_type = png_data[idx + 4 : idx + 8].decode()
        idx += chunk_len + 12
        if chunk_type == "IEND":
            break
    return idx - orig


def get_png(data_stream: BinaryIO) -> bytes:
    """Extract a PNG image from a binary stream.

    Reads from the current position until the IEND chunk is found.

    Args:
        data_stream: Binary stream positioned at the start of PNG data.

    Returns:
        The complete PNG image as bytes.

    Raises:
        AssertionError: If the stream does not contain a valid PNG signature.
    """
    origin_pos = data_stream.tell()
    assert data_stream.read(8) == b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a"
    while True:
        length = load_type(data_stream, ">I")
        chunk_type = data_stream.read(4)
        data_stream.read(length + 4)
        if chunk_type == b"IEND":
            break
    end_pos = data_stream.tell()
    data_stream.seek(origin_pos)
    png_data = data_stream.read(end_pos - origin_pos)
    return png_data
