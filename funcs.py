
import struct
from msgpack import packb, unpackb

def load_length(data_stream, struct_type):
    length = struct.unpack(struct_type, data_stream.read(struct.calcsize(struct_type)))[0]
    return data_stream.read(length)

def load_type(data_stream, struct_type):
    return struct.unpack(struct_type, data_stream.read(struct.calcsize(struct_type)))[0]

def msg_unpack(data):
    return unpackb(data, raw=False)

def msg_pack(data):
    serialized = packb(data, use_single_float=True, use_bin_type=True)
    return serialized, len(serialized)

def get_png_length(png_data, orig=0):
    idx = orig
    assert png_data[idx:idx+8] == b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'

    idx += 8
    while True:
        chunk_len = struct.unpack('>I', png_data[idx:idx + 4])[0]
        chunk_type = png_data[idx + 4:idx + 8].decode()
        idx += chunk_len + 12
        if chunk_type == 'IEND':
            break
    return idx-orig