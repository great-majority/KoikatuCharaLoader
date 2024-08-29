import struct

import kkloader
import kkloader.KoikatuCharaData
from kkloader.funcs import get_png, load_length, load_type


class EmocreCharaData(kkloader.KoikatuCharaData):
    def __init__(self):
        self.modules = {
            "Custom": kkloader.kk_Custom,
            "Coordinate": kkloader.kk_Coordinate,
            "Parameter": kkloader.kk_Parameter,
            "Status": kkloader.kk_Status,
            "About": kkloader.kk_About,
            "KKEx": kkloader.kk_KKEx,
        }

    def _load_header(self, data, **kwargs):
        self.image = get_png(data)
        self.product_no = load_type(data, "i")
        self.header = load_length(data, "b")
        self.version = load_length(data, "b")
        self.language = load_type(data, "i")
        self.userid = load_length(data, "b")
        self.dataid = load_length(data, "b")
        package_length = load_type(data, "i")
        self.packages = []
        for i in range(package_length):
            self.packages.append(load_type(data, "i"))

    def _make_bytes_header(self):
        ipack = struct.Struct("i")
        bpack = struct.Struct("b")
        packages = b"".join(list(map(lambda x: ipack.pack(x), self.packages)))
        data = b"".join(
            [
                self.image,
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
                ipack.pack(len(self.packages)),
                packages,
            ]
        )
        return data

    def _make_dict_header(self, **kwargs):
        data = {
            "product_no": self.product_no,
            "header": self.header.decode("utf-8"),
            "version": self.version.decode("utf-8"),
            "blockdata": self.blockdata,
            "userid": self.userid.decode("utf-8"),
            "dataid": self.dataid.decode("utf-8"),
            "language": self.language,
            "packages": self.packages,
        }
        return data

    def __str__(self):
        header = self.header.decode("utf-8")
        userid = self.userid.decode("ascii")
        dataid = self.dataid.decode("ascii")
        return "{}, {}, userid:{}, dataid:{}".format(header, self["Parameter"]["fullname"], userid, dataid)
