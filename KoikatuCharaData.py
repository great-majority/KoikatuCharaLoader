#!/usr/bin/env python

import struct
import msgpack
import io
import json

class KoikatuCharaData:
    def __init__(self, filename):
        data = None
        with open(filename, "br") as f:
            data = f.read()

        self.png_length = self._get_png_length(data)
        data_stream = io.BytesIO(data)
        self.png_data = data_stream.read(self.png_length)
        self.product_no = struct.unpack("i", data_stream.read(4))[0] # 100
        data_stream.read(20) # b"\x12【KoiKatuChara】\x05"
        self.version = data_stream.read(5).decode("ascii") # "0.0.0"
        face_png_length = struct.unpack("i", data_stream.read(4))[0]
        self.face_png_data = data_stream.read(face_png_length)

        blockdata_size = struct.unpack("i", data_stream.read(4))[0]
        self.blockdata = msgpack.unpackb(data_stream.read(blockdata_size), raw=False)
        charadata_size = struct.unpack("q", data_stream.read(8))[0]

        data = data_stream.read()
        for i in self.blockdata["lstInfo"]:
            data_part = data[i["pos"]:i["pos"]+i["size"]]
            if i["name"] == "Custom":
                self._load_custom(data_part)
            elif i["name"] == "Coordinate":
                self._load_coordinate(data_part)
            elif i["name"] == "Parameter":
                self.parameter = msgpack.unpackb(data_part, raw=False)
            elif i["name"] == "Status":
                self.status = msgpack.unpackb(data_part, raw=False)

    def save(self, filename):
        custom_s = self._serialize_custom()
        coordinate_s = self._serialize_coordinates()
        parameter_s = msgpack.packb(self.parameter, use_single_float=True, use_bin_type=True)
        status_s = msgpack.packb(self.status, use_single_float=True, use_bin_type=True)
        chara_values = b"".join([
            custom_s,
            coordinate_s,
            parameter_s,
            status_s
        ])

        pos = 0
        for i,n in enumerate(self.blockdata["lstInfo"]):
            if n["name"] == "Custom":
                self.blockdata["lstInfo"][i]["pos"] = pos
                self.blockdata["lstInfo"][i]["size"] = len(custom_s)
                pos += len(custom_s)
            elif n["name"] == "Coordinate":
                self.blockdata["lstInfo"][i]["pos"] = pos
                self.blockdata["lstInfo"][i]["size"] = len(coordinate_s)
                pos += len(coordinate_s)
            elif n["name"] == "Parameter":
                self.blockdata["lstInfo"][i]["pos"] = pos
                self.blockdata["lstInfo"][i]["size"] = len(parameter_s)
                pos += len(parameter_s)
            elif n["name"] == "Status":
                self.blockdata["lstInfo"][i]["pos"] = pos
                self.blockdata["lstInfo"][i]["size"] = len(status_s)
                pos += len(status_s)
        blockdata_s = msgpack.packb(self.blockdata, use_single_float=True, use_bin_type=True)

        data = b"".join([
            self.png_data,
            struct.pack("i", self.product_no),
            b"\x12"+"【KoiKatuChara】".encode("utf-8")+b"\x05",
            self.version.encode("ascii"),
            struct.pack("i", len(self.face_png_data)),
            self.face_png_data,
            struct.pack("i", len(blockdata_s)),
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

    def _load_custom(self, data):
        data_stream = io.BytesIO(data)
        length = struct.unpack("i", data_stream.read(4))[0]
        self.face = msgpack.unpackb(data_stream.read(length), raw=False)
        length = struct.unpack("i", data_stream.read(4))[0]
        self.body = msgpack.unpackb(data_stream.read(length), raw=False)
        length = struct.unpack("i", data_stream.read(4))[0]
        self.hair = msgpack.unpackb(data_stream.read(length), raw=False)

    def _serialize_custom(self):
        face_s = msgpack.packb(self.face, use_single_float=True, use_bin_type=True)
        body_s = msgpack.packb(self.body, use_single_float=True, use_bin_type=True)
        hair_s = msgpack.packb(self.hair, use_single_float=True, use_bin_type=True)
        data = [
            struct.pack("i", len(face_s)),
            face_s,
            struct.pack("i", len(body_s)),
            body_s,
            struct.pack("i", len(hair_s)),
            hair_s
        ]
        return b"".join(data)

    def _load_coordinate(self, data):
        self.coordinates = []
        for c in msgpack.unpackb(data):
            coordinate = {}
            data_stream = io.BytesIO(c)
            length = struct.unpack("i", data_stream.read(4))[0]
            coordinate["clothes"] = msgpack.unpackb(data_stream.read(length), raw=False)
            length = struct.unpack("i", data_stream.read(4))[0]
            coordinate["accessory"] = msgpack.unpackb(data_stream.read(length), raw=False)
            makeup = struct.unpack("b", data_stream.read(1))[0] 
            coordinate["enableMakeup"] = True if makeup != 0 else False
            length = struct.unpack("i", data_stream.read(4))[0]
            coordinate["makeup"] = msgpack.unpackb(data_stream.read(length), raw=False)
            self.coordinates.append(coordinate)
    
    def _serialize_coordinates(self):
        data = []
        for i in self.coordinates:
            cloth_s = msgpack.packb(i["clothes"], use_single_float=True, use_bin_type=True)
            accessory_s = msgpack.packb(i["accessory"], use_single_float=True, use_bin_type=True)
            makeup_s = msgpack.packb(i["makeup"], use_single_float=True, use_bin_type=True, strict_types=True)
            coordinate = [
                struct.pack("i", len(cloth_s)),
                cloth_s,
                struct.pack("i", len(accessory_s)),
                accessory_s,
                struct.pack("b", 1) if i["enableMakeup"] else struct.pack("b", 0),
                struct.pack("i", len(makeup_s)),
                makeup_s
            ]
            data.append(b"".join(coordinate))
        return msgpack.packb(data, use_bin_type=True)

def main():
    k = KoikatuCharaData("sa.png")
    #print(json.dumps(k.coordinates[0]["makeup"], indent=2))
    k.save("si.png")

if __name__ == '__main__':
    main()