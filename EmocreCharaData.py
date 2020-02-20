# -*- coding:utf-8 -*-

import struct
from KoikatuCharaData import Custom, Parameter, Status
from funcs import load_length, load_type, msg_pack, msg_unpack, get_png_length
import io
import json
import base64

class EmocreCharaData:
    value_order = ["Custom", "Coordinate", "Parameter", "Status"]

    def __init__(self, filename):
        data = None
        with open(filename, "br") as f:
            data = f.read()
        
        length = get_png_length(data)
        data_stream = io.BytesIO(data)
        
        self.png_data = data_stream.read(length)
        self.product_no = load_type(data_stream, "i")
        self.header = load_length(data_stream, "b")
        self.version = load_length(data_stream, "b")
        self.language = load_type(data_stream, "i")
        self.userid = load_length(data_stream, "b")
        self.dataid = load_length(data_stream, "b")
        tag_length = load_type(data_stream, "i")
        self.tags = []
        for i in range(tag_length):
            self.tags.append(load_type(data_stream, "i"))
        self._blockdata = msg_unpack(load_length(data_stream, "i"))
        lstinfo_raw = load_length(data_stream, "q")

        for i in self._blockdata["lstInfo"]:
            data_part = lstinfo_raw[i["pos"]:i["pos"]+i["size"]]
            if i["name"] in globals():
                setattr(self, i["name"], globals()[i["name"]](data_part))
                # for backward compatibility
                setattr(self, i["name"].lower(), getattr(self, i["name"]).jsonalizable())
            else:
                raise ValueError("unsupported lstinfo: %s"%i["name"])
    
    def save(self, filename):
        cumsum = 0
        chara_values = []
        for i,v in enumerate(self.value_order):
            serialized, length = getattr(self, v).serialize()
            self._blockdata["lstInfo"][i]["pos"] = cumsum
            self._blockdata["lstInfo"][i]["size"] = length
            chara_values.append(serialized)
            cumsum += length
        chara_values = b"".join(chara_values)
        blockdata_s, blockdata_l = msg_pack(self._blockdata)

        ipack = struct.Struct("i")
        bpack = struct.Struct("b")
        tags = b"".join(list(map(lambda x: ipack.pack(x), self.tags)))
        data = b"".join([
            self.png_data,
            ipack.pack(self.product_no),
            bpack.pack(len(self.header)),
            self.header,
            bpack.pack(len(self.version)),
            self.version,
            ipack.pack(self.language),
            bpack.pack(len(self.userid)),
            self.userid,
            bpack.pack(len(self.dataid)),
            self.dataid,
            ipack.pack(len(self.tags)),
            tags,
            ipack.pack(blockdata_l),
            blockdata_s,
            struct.pack("q", len(chara_values)),
            chara_values
        ])

        with open(filename, "bw+") as f:
            f.write(data)
        
    def save_json(self, filename, include_image=False):
        datas = {
            "product_no": self.product_no,
            "header": self.header.decode("utf-8"),
            "version": self.version.decode("utf-8"),
            "userid": self.userid.decode("utf-8"),
            "dataid": self.dataid.decode("utf-8"),
            "language": self.language,
            "tags": self.tags
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

class Coordinate(Custom):
    def __init__(self, data):
        data_stream = io.BytesIO(data)
        self.fields = ["colthes", "accessory"]
        for f in self.fields:
            setattr(self, f, msg_unpack(load_length(data_stream, "i")))