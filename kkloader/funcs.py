import struct

from msgpack import packb, unpackb
from msgpack.fallback import Packer as PurePacker


def load_length(data_stream, struct_type):
    length = struct.unpack(struct_type, data_stream.read(struct.calcsize(struct_type)))[0]
    return data_stream.read(length)


def load_string(data_stream):
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


def load_type(data_stream, struct_type):
    return struct.unpack(struct_type, data_stream.read(struct.calcsize(struct_type)))[0]


def write_string(data_stream, value):
    length_bytes = b""
    length = len(value)
    while True:
        serial = length & 0b1111111
        if length >> 7 != 0:
            length = length >> 7
            length_bytes += struct.pack("b", 0b10000000 | serial)
        else:
            length_bytes += struct.pack("b", serial)
            break
    data_stream.write(length_bytes)
    data_stream.write(value)


def msg_unpack(data):
    return unpackb(data, raw=False, strict_map_key=False)


def msg_pack(data):
    serialized = packb(data, use_single_float=True, use_bin_type=True)
    return serialized, len(serialized)


class KKExPacker(PurePacker):
    KEYS_TO_OVERRIDE = {
        "CurrentCrest",
        "BreathingBPM",
        "ResizeCentroid",
        "clothingOffsetVersion",
        "InmonLevel",
        "SemenVolume",
        "ReferralIndex",
        "MenstruationSchedule",
        "EnableBulge",
        "AllCharaOverlayTable",
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        "LeaveSchoolWeek",
        "ReturnToSchoolWeek",
    }

    def _pack_map_pairs(self, n, pairs, nest_limit):
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


def msg_pack_kkex(data):
    packer = KKExPacker(use_single_float=True, use_bin_type=True)
    serialized = packer.pack(data)
    return serialized, len(serialized)


def get_png_length(png_data, orig=0):
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


def get_png(data_stream):
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
