import io
import struct

import kkloader.KoikatuCharaData
from kkloader.funcs import load_length, msg_pack, msg_unpack
from kkloader.KoikatuCharaData import BlockData


class HoneycomeCharaData(kkloader.KoikatuCharaData):
    def __init__(self):
        self.modules = {
            "Custom": Custom,
            "Coordinate": Coordinate,
            "Parameter": kkloader.kk_Parameter,
            "Status": kkloader.kk_Status,
            "Graphic": Graphic,
            "About": kkloader.kk_About,
            "GameParameter_HCP": GameParameter_HCP,
            "GameInfo_HCP": GameInfo_HCP,
            "GameParameter_HC": GameParameter_HC,
            "GameInfo_HC": GameInfo_HC,
        }


class Custom(BlockData):
    fields = ["face", "body"]

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
    fields = [
        "clothes",
        "accessory",
        "makeup",
        "hair",
        "nail",
    ]

    def __init__(self, data, version):
        self.name = "Coordinate"
        self.version = version
        if data is None:
            return

        self.data = []
        for coordinate_bytes in msg_unpack(data):
            data_stream = io.BytesIO(coordinate_bytes)
            coordinate_dict = {}
            for f in self.fields:
                coordinate_dict[f] = msg_unpack(load_length(data_stream, "i"))
            self.data.append(coordinate_dict)

    def serialize(self):
        data = []
        for i in self.data:
            c = []
            pack = struct.Struct("i")

            for f in self.fields:
                serialized, length = msg_pack(i[f])
                c.extend([pack.pack(length), serialized])

            data.append(b"".join(c))
        serialized_all, _ = msg_pack(data)

        return serialized_all, self.name, self.version


class Graphic(BlockData):
    def __init__(self, data, version):
        super().__init__(name="Graphic", data=data, version=version)


class GameParameter_HCP(BlockData):
    def __init__(self, data, version):
        super().__init__(name="GameParameter_HCP", data=data, version=version)


class GameInfo_HCP(BlockData):
    def __init__(self, data, version):
        super().__init__(name="GameInfo_HCP", data=data, version=version)


class GameParameter_HC(BlockData):
    def __init__(self, data, version):
        super().__init__(name="GameParameter_HC", data=data, version=version)


class GameInfo_HC(BlockData):
    def __init__(self, data, version):
        super().__init__(name="GameInfo_HC", data=data, version=version)
