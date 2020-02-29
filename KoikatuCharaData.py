# -*- coding:utf-8 -*-

import struct
from .funcs import load_length, load_type, msg_pack, msg_unpack, get_png
import io
import json
import base64

class KoikatuCharaData:
    value_order = ["Custom", "Coordinate", "Parameter", "Status"]
    
    def __init__(self):
        pass

    @staticmethod
    def load(filelike, contains_png=True):
        kc = KoikatuCharaData()

        if isinstance(filelike, str):
            with open(filelike, "br") as f:
                data = f.read()
            data_stream = io.BytesIO(data)

        elif isinstance(filelike, bytes):
            data_stream = io.BytesIO(filelike)

        elif isinstance(filelike, io.BytesIO):
            data_stream = filelike
        
        else:
            ValueError("unsupported input. type:{}".format(type(filelike)))

        kc.png_data = None 
        if contains_png:
            kc.png_data = get_png(data_stream)

        kc.product_no = load_type(data_stream, "i") # 100
        kc.header = load_length(data_stream, "b") # 【KoiKatuChara】
        kc.version = load_length(data_stream, "b") # 0.0.0
        kc.face_png_data = load_length(data_stream, "i")
        kc.blockdata = msg_unpack(load_length(data_stream, "i"))
        lstinfo_raw = load_length(data_stream, "q")

        for i in kc.blockdata["lstInfo"]:
            data_part = lstinfo_raw[i["pos"]:i["pos"]+i["size"]]
            if i["name"] in globals():
                setattr(kc, i["name"], globals()[i["name"]](data_part))
                # for backward compatibility
                setattr(kc, i["name"].lower(), getattr(kc, i["name"]).jsonalizable())
            else:
                raise ValueError("unsupported lstinfo: %s"%i["name"])
        return kc

    def __bytes__(self):
        cumsum = 0
        chara_values = []
        for i,v in enumerate(self.value_order):
            serialized, length = getattr(self, v).serialize()
            self.blockdata["lstInfo"][i]["pos"] = cumsum
            self.blockdata["lstInfo"][i]["size"] = length
            chara_values.append(serialized)
            cumsum += length
        chara_values = b"".join(chara_values)
        blockdata_s, blockdata_l = msg_pack(self.blockdata)

        ipack = struct.Struct("i")
        bpack = struct.Struct("b")
        data_chunks = []
        if self.png_data:
            data_chunks.append(self.png_data)
        data_chunks.extend([
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
        data = b"".join(data_chunks)
        return data

    def save(self, filename):
        data = bytes(self)
        with open(filename, "bw+") as f:
            f.write(data)
        
    def save_json(self, filename, include_image=False):
        datas = {
            "product_no": self.product_no,
            "header": self.header.decode("utf-8"),
            "version": self.version.decode("utf-8"),
            "blockdata": self.blockdata
        }
        for v in self.value_order:
            datas.update({v.lower(): getattr(self, v).jsonalizable()})
        
        if include_image:
            datas.update({"png_image": base64.b64encode(self.png_data).decode("ascii")})
            datas.update({"face_png_image": base64.b64encode(self.face_png_data).decode("ascii")})

        def bin_to_str(serial):
            if isinstance(serial, io.BufferedRandom) or isinstance(serial, bytes):
                return base64.b64encode(bytes(serial)).decode("ascii")
            else:
                raise TypeError("{} is not JSON serializable".format(serial))

        with open(filename, "w+") as f:
            json.dump(datas, f, indent=2, default=bin_to_str)
    
    def __str__(self):
        header = self.header.decode("utf-8")
        name = "{} {} ( {} )".format(
            self.parameter["lastname"],
            self.parameter["firstname"],
            self.parameter["nickname"]
        )
        return "{}, {}".format(header, name)

class Custom:
    def __init__(self, data):
        data_stream = io.BytesIO(data)
        self.fields = ["face", "body", "hair"]
        for f in self.fields:
            setattr(self, f, msg_unpack(load_length(data_stream, "i")))

    def serialize(self):
        data = []
        pack = struct.Struct("i")
        for f in self.fields:
            field_s, length = msg_pack(getattr(self, f))
            data.append(pack.pack(length))
            data.append(field_s)
        serialized = b"".join(data)
        return serialized, len(serialized)
    
    def jsonalizable(self):
        data = {}
        for f in self.fields:
            data.update({f: getattr(self, f)})
        return data

class Coordinate:
    def __init__(self, data=None):
        if data is None:
            return
        self.coordinates = []
        for c in msg_unpack(data):
            coordinate = {}
            data_stream = io.BytesIO(c)
            coordinate["clothes"] = msg_unpack(load_length(data_stream, "i"))
            coordinate["accessory"] = msg_unpack(load_length(data_stream, "i"))
            coordinate["enableMakeup"] = bool(load_type(data_stream, "b"))
            coordinate["makeup"] = msg_unpack(load_length(data_stream, "i"))
            self.coordinates.append(coordinate)
    
    def serialize(self):
        data = []
        for i in self.coordinates:
            c = []
            pack = struct.Struct("i")

            serialized, length = msg_pack(i["clothes"])
            c.extend([pack.pack(length), serialized])

            serialized, length = msg_pack(i["accessory"])
            c.extend([pack.pack(length), serialized])

            c.append(struct.pack("b", i["enableMakeup"]))
            
            serialized, length = msg_pack(i["makeup"])
            c.extend([pack.pack(length), serialized])
            
            data.append(b"".join(c))
        serialized_all, length = msg_pack(data)
        return serialized_all, length
    
    def jsonalizable(self):
        return self.coordinates

class Parameter:
    def __init__(self, data):
        self.parameter = msg_unpack(data)
    def serialize(self):
        serialized, length = msg_pack(self.parameter)
        return serialized, length
    def jsonalizable(self):
        return self.parameter

class Status:
    def __init__(self, data):
        self.status = msg_unpack(data)
    def serialize(self):
        serialized, length = msg_pack(self.status)
        return serialized, length
    def jsonalizable(self):
        return self.status
