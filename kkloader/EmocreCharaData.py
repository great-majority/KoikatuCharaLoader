# -*- coding:utf-8 -*-

import base64
import io
import json
import struct

import kkloader.KoikatuCharaData as kcl
from kkloader.funcs import get_png, load_length, load_type, msg_pack, msg_unpack


class EmocreCharaData:
    value_order = ["Custom", "Coordinate", "Parameter", "Status"]

    def __init__(self):
        pass

    @staticmethod
    def load(filelike):
        ec = EmocreCharaData()

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

        ec.png_data = get_png(data_stream)
        ec.product_no = load_type(data_stream, "i")
        ec.header = load_length(data_stream, "b")
        ec.version = load_length(data_stream, "b")
        ec.language = load_type(data_stream, "i")
        ec.userid = load_length(data_stream, "b")
        ec.dataid = load_length(data_stream, "b")
        tag_length = load_type(data_stream, "i")
        ec.packages = []
        for i in range(tag_length):
            ec.packages.append(load_type(data_stream, "i"))
        ec.blockdata = msg_unpack(load_length(data_stream, "i"))
        lstinfo_raw = load_length(data_stream, "q")

        ec.unknown_datapart_names = []
        for i in ec.blockdata["lstInfo"]:
            data_part = lstinfo_raw[i["pos"] : i["pos"] + i["size"]]
            if i["name"] in EmocreCharaData.value_order:
                if i["name"] == "Coordinate":
                    setattr(ec, i["name"], Coordinate(data_part))
                else:
                    setattr(ec, i["name"], getattr(kcl, i["name"])(data_part))
                # for backward compatibility
                setattr(ec, i["name"].lower(), getattr(ec, i["name"]).jsonalizable())
            else:
                raise ValueError("unsupported lstinfo: %s" % i["name"])

        return ec

    def __bytes__(self):
        cumsum = 0
        chara_values = []
        for i, v in enumerate(self.value_order):
            serialized, length = getattr(self, v).serialize()
            self.blockdata["lstInfo"][i]["pos"] = cumsum
            self.blockdata["lstInfo"][i]["size"] = length
            chara_values.append(serialized)
            cumsum += length
        chara_values = b"".join(chara_values)
        blockdata_s, blockdata_l = msg_pack(self.blockdata)

        ipack = struct.Struct("i")
        bpack = struct.Struct("b")
        tags = b"".join(list(map(lambda x: ipack.pack(x), self.tags)))
        data = b"".join(
            [
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
                chara_values,
            ]
        )
        return data

    def save(self, filename):
        data = self.__bytes__()
        with open(filename, "bw+") as f:
            f.write(data)

    def save_json(self, filename, include_image=False):
        datas = {
            "product_no": self.product_no,
            "header": self.header.decode("utf-8"),
            "version": self.version.decode("utf-8"),
            "blockdata": self.blockdata,
            "userid": self.userid.decode("utf-8"),
            "dataid": self.dataid.decode("utf-8"),
            "language": self.language,
            "tags": self.tags,
        }
        for v in self.value_order:
            datas.update({v.lower(): getattr(self, v).jsonalizable()})

        if include_image:
            datas.update({"png_image": base64.b64encode(self.png_data).decode("ascii")})

        def bin_to_str(serial):
            if isinstance(serial, io.BufferedRandom) or isinstance(serial, bytes):
                return base64.b64encode(bytes(serial)).decode("ascii")
            else:
                raise TypeError("{} is not JSON serializable".format(serial))

        with open(filename, "w+") as f:
            json.dump(datas, f, indent=2, default=bin_to_str)

    def __str__(self):
        header = self.header.decode("utf-8")
        userid = self.userid.decode("ascii")
        dataid = self.dataid.decode("ascii")
        return "{}, {}, userid:{}, dataid:{}".format(
            header, self.parameter["fullname"], userid, dataid
        )


class Coordinate(kcl.Custom):
    fields = ["clothes", "accessory"]

    def __init__(self, data=None):
        if data is None:
            return
        data_stream = io.BytesIO(data)
        for f in self.fields:
            setattr(self, f, msg_unpack(load_length(data_stream, "i")))
