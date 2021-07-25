# -*- coding:utf-8 -*-

import base64
import io
import json
import struct

from kkloader.funcs import get_png, load_length, load_type, msg_pack, msg_unpack


class KoikatuCharaData:
    readable_formats = ["Custom", "Coordinate", "Parameter", "Status"]

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

        kc.image = None
        if contains_png:
            kc.image = get_png(data_stream)

        kc.product_no = load_type(data_stream, "i")  # 100
        kc.header = load_length(data_stream, "b")  # 【KoiKatuChara】
        kc.version = load_length(data_stream, "b")  # 0.0.0
        kc.face_image = load_length(data_stream, "i")
        lstinfo_index = msg_unpack(load_length(data_stream, "i"))
        lstinfo_raw = load_length(data_stream, "q")

        kc.unknown_blockdata = []
        kc.blockdata = []
        for i in lstinfo_index["lstInfo"]:
            name = i["name"]
            pos = i["pos"]
            size = i["size"]
            version = i["version"]
            data = lstinfo_raw[pos : pos + size]

            kc.blockdata.append(name)
            if name in kc.readable_formats:
                setattr(kc, name, globals()[name](data, version))
            else:
                setattr(kc, name, UnknownBlockData(name, data, version))
                kc.unknown_blockdata.append(name)
        return kc

    def __bytes__(self):
        cumsum = 0
        chara_values = []
        lstinfos = []
        for v in self.blockdata:
            data, name, version = getattr(self, v).serialize()
            lstinfos.append(
                {"name": name, "version": version, "pos": cumsum, "size": len(data)}
            )
            chara_values.append(data)
            cumsum += len(data)
        chara_values = b"".join(chara_values)
        blockdata_s, blockdata_l = msg_pack({"lstInfo": lstinfos})

        ipack = struct.Struct("i")
        bpack = struct.Struct("b")
        data_chunks = []
        if self.image:
            data_chunks.append(self.image)
        data_chunks.extend(
            [
                ipack.pack(self.product_no),
                bpack.pack(len(self.header)),
                self.header,
                bpack.pack(len(self.version)),
                self.version,
                ipack.pack(len(self.face_image)),
                self.face_image,
                ipack.pack(blockdata_l),
                blockdata_s,
                struct.pack("q", len(chara_values)),
                chara_values,
            ]
        )
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
            "blockdata": self.blockdata,
        }
        for v in self.blockdata:
            datas.update({v: getattr(self, v).jsonalizable()})

        if include_image:
            datas.update({"image": base64.b64encode(self.image).decode("ascii")})
            datas.update(
                {"face_image": base64.b64encode(self.face_image).decode("ascii")}
            )

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
            self.parameter["nickname"],
        )
        return "{}, {}".format(header, name)

    def __getitem__(self, key):
        if key in self.blockdata:
            return getattr(self, key)
        else:
            raise ValueError("no such blockdata.")


class BlockData:
    def __init__(self, name="Blockdata", data=None, version="0.0.0"):
        self.name = name
        self.data = msg_unpack(data)
        self.version = version

    def serialize(self):
        data, _ = msg_pack(self.data)
        return data, self.name, self.version

    def jsonalizable(self):
        return self.data

    def __getitem__(self, key):
        return self.data[key]


class Custom(BlockData):
    fields = ["face", "body", "hair"]

    def __init__(self, data, version):
        self.name = "Custom"
        self.version = version
        self.data = {}
        data_stream = io.BytesIO(data)
        for f in self.fields:
            self.data[f] = msg_unpack(load_length(data_stream, "i"))

    def serialize(self):
        data = []
        pack = struct.Struct("i")
        for f in self.fields:
            field_s, length = msg_pack(self.data[f])
            data.append(pack.pack(length))
            data.append(field_s)
        serialized = b"".join(data)
        return serialized, self.name, self.version


class Coordinate(BlockData):
    def __init__(self, data, version):
        self.name = "Coordinate"
        self.version = version
        if data is None:
            return
        self.data = []
        for c in msg_unpack(data):
            data_stream = io.BytesIO(c)
            c = {
                "clothes": msg_unpack(load_length(data_stream, "i")),
                "accessory": msg_unpack(load_length(data_stream, "i")),
                "enableMakeup": bool(load_type(data_stream, "b")),
                "makeup": msg_unpack(load_length(data_stream, "i")),
            }
            self.data.append(c)

    def serialize(self):
        data = []
        for i in self.data:
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
        return serialized_all, self.name, self.version


class Parameter(BlockData):
    def __init__(self, data, version):
        super().__init__(name="Parameter", data=data, version=version)


class Status(BlockData):
    def __init__(self, data, version):
        super().__init__(name="Status", data=data, version=version)


class UnknownBlockData(BlockData):
    def __init__(self, data, name, version):
        self.data = data
        self.name = name
        self.version = version

    def serialize(self):
        return self.data, self.name, self.version
