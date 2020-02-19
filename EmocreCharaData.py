# -*- coding:utf-8 -*-

import struct
from KoikatuCharaData import Custom, Parameter, Status
from funcs import load_length, load_type, msg_pack, msg_unpack, get_png_length
import io
import json
import base64

class EmocreCharaData:
    
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
        pass

class Coordinate(Custom):
    def __init__(self, data):
        data_stream = io.BytesIO(data)
        self.fields = ["colthes", "accessory"]
        for f in self.fields:
            setattr(self, f, msg_unpack(load_length(data_stream, "i")))