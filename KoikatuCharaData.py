#!/usr/bin/env python

import struct
from msgpack import packb, unpackb
import io
import json

def _load_length(data_stream, struct_type):
    length = struct.unpack(struct_type, data_stream.read(struct.calcsize(struct_type)))[0]
    return data_stream.read(length)

def _load_type(data_stream, struct_type):
    return struct.unpack(struct_type, data_stream.read(struct.calcsize(struct_type)))[0]

def _msg_unpack(data):
    return unpackb(data, raw=False)

def _msg_pack(data):
    serialized = packb(data, use_single_float=True, use_bin_type=True)
    return serialized, len(serialized)

class KoikatuCharaData:
    def __init__(self, filename):
        data = None
        with open(filename, "br") as f:
            data = f.read()
        
        length = self._get_png_length(data)
        data_stream = io.BytesIO(data)
        
        self.png_data = data_stream.read(length)
        self.product_no = _load_type(data_stream, "i") # 100
        self.header = _load_length(data_stream, "b") # 【KoiKatuChara】
        self.version = _load_length(data_stream, "b") # 0.0.0
        self.face_png_data = _load_length(data_stream, "i")
        self._blockdata = _msg_unpack(_load_length(data_stream, "i"))
        lstinfo_raw = _load_length(data_stream, "q")

        for i in self._blockdata["lstInfo"]:
            data_part = lstinfo_raw[i["pos"]:i["pos"]+i["size"]]
            if i["name"] in globals():
                setattr(self, i["name"], globals()[i["name"]](data_part))
            else:
                raise ValueError("unsupported lstinfo: %s"%i["name"])

    def save(self, filename):
        cumsum = 0
        value_order = ["Custom", "Coordinate", "Parameter", "Status"]
        chara_values = []
        for i,v in enumerate(value_order):
            serialized, length = getattr(self, v).serialize()
            self._blockdata["lstInfo"][i]["pos"] = cumsum
            self._blockdata["lstInfo"][i]["size"] = length
            chara_values.append(serialized)
            cumsum += length
        chara_values = b"".join(chara_values)
        blockdata_s, blockdata_l = _msg_pack(self._blockdata)

        ipack = struct.Struct("i")
        bpack = struct.Struct("b")
        data = b"".join([
            self.png_data,
            ipack.pack(self.product_no),
            bpack.pack(len(self.header)),
            self.header,
            bpack.pack(len(self.version)),
            self.version,
            ipack.pack(len(self.face_png_data)),
            self.face_png_data,
            ipack.pack(blockdata_l),
            blockdata_s,
            struct.pack("q", len(chara_values)),
            chara_values
        ])

        with open(filename, "bw+") as f:
            f.write(data)

    def _get_png_length(self, png_data, orig=0):
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
    
    def __str__(self):
        header = self.header.decode("utf-8")
        name = "{} {} ( {} )".format(
            self.Parameter.parameter["lastname"],
            self.Parameter.parameter["firstname"],
            self.Parameter.parameter["nickname"]
        )
        return "{}: {}".format(header, name)

class Custom:
    def __init__(self, data):
        data_stream = io.BytesIO(data)
        self.fields = ["face", "body", "hair"]
        for f in self.fields:
            setattr(self, f, _msg_unpack(_load_length(data_stream, "i")))

    def serialize(self):
        data = []
        pack = struct.Struct("i")
        for f in self.fields:
            field_s, length = _msg_pack(getattr(self, f))
            data.append(pack.pack(length))
            data.append(field_s)
        serialized = b"".join(data)
        return serialized, len(serialized)

class Coordinate:
    def __init__(self, data):
        self.coordinates = []
        for c in _msg_unpack(data):
            coordinate = {}
            data_stream = io.BytesIO(c)
            coordinate["clothes"] = _msg_unpack(_load_length(data_stream, "i"))
            coordinate["accessory"] = _msg_unpack(_load_length(data_stream, "i"))
            coordinate["enableMakeup"] = bool(_load_type(data_stream, "b"))
            coordinate["makeup"] = _msg_unpack(_load_length(data_stream, "i"))
            self.coordinates.append(coordinate)
    
    def serialize(self):
        data = []
        for i in self.coordinates:
            c = []
            pack = struct.Struct("i")

            serialized, length = _msg_pack(i["clothes"])
            c.extend([pack.pack(length), serialized])

            serialized, length = _msg_pack(i["accessory"])
            c.extend([pack.pack(length), serialized])

            c.append(struct.pack("b", i["enableMakeup"]))
            
            serialized, length = _msg_pack(i["makeup"])
            c.extend([pack.pack(length), serialized])
            
            data.append(b"".join(c))
        serialized_all, length = _msg_pack(data)
        return serialized_all, length

class Parameter:
    def __init__(self, data):
        self.parameter = _msg_unpack(data)
    def serialize(self):
        serialized, length = _msg_pack(self.parameter)
        return serialized, length

class Status:
    def __init__(self, data):
        self.status = _msg_unpack(data)
    def serialize(self):
        serialized, length = _msg_pack(self.status)
        return serialized, length
