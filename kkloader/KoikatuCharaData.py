# -*- coding:utf-8 -*-

import base64
import copy
import io
import json
import struct

from kkloader.funcs import get_png, load_length, load_type, msg_pack, msg_pack_kkex, msg_unpack

import lz4.block
import msgpack


def bin_to_str(serial):
    if isinstance(serial, io.BufferedRandom) or isinstance(serial, bytes):
        return base64.b64encode(bytes(serial)).decode("ascii")
    else:
        raise TypeError("{} is not JSON serializable".format(serial))


class KoikatuCharaData:
    def __init__(self):
        self.modules = {
            "Custom": Custom,
            "Coordinate": Coordinate,
            "Parameter": Parameter,
            "Status": Status,
            "About": About,
            "KKEx": KKEx,
        }

    @classmethod
    def load(cls, filelike, contains_png=True):
        kc = cls()

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

        kc._load_header(data_stream, contains_image=contains_png)
        kc._load_blockdata(data_stream)

        return kc

    def _load_header(self, data, **kwargs):
        self.image = None
        if "contains_image" in kwargs and kwargs["contains_image"]:
            self.image = get_png(data)

        self.product_no = load_type(data, "i")  # 100
        self.header = load_length(data, "b")  # 【KoiKatuChara】
        self.version = load_length(data, "b")  # 0.0.0
        self.face_image = load_length(data, "i")

    def _load_blockdata(self, data):
        lstinfo_index = msg_unpack(load_length(data, "i"))
        lstinfo_raw = load_length(data, "q")

        self.unknown_blockdata = []
        self.blockdata = []
        self.original_lstinfo_order = list(map(lambda x: x["name"], lstinfo_index["lstInfo"]))
        self.serialized_lstinfo_order = list(map(lambda x: x["name"], sorted(lstinfo_index["lstInfo"], key=lambda x: x["pos"])))

        for i in lstinfo_index["lstInfo"]:
            name = i["name"]
            pos = i["pos"]
            size = i["size"]
            version = i["version"]
            data = lstinfo_raw[pos : pos + size]

            self.blockdata.append(name)
            if name in self.modules.keys():
                setattr(self, name, self.modules[name](data, version))
            else:
                setattr(self, name, UnknownBlockData(name, data, version))
                self.unknown_blockdata.append(name)

    def __bytes__(self):
        header_bytes = self._make_bytes_header()
        blockdata_bytes = self._make_bytes_blockdata()
        return header_bytes + blockdata_bytes

    def _make_bytes_header(self):
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
            ]
        )
        return b"".join(data_chunks)

    def _make_bytes_blockdata(self):
        cumsum = 0
        chara_values = []
        lstinfos = []
        for v in self.serialized_lstinfo_order:
            data, name, version = getattr(self, v).serialize()
            lstinfos.append({"name": name, "version": version, "pos": cumsum, "size": len(data)})
            chara_values.append(data)
            cumsum += len(data)
        chara_values = b"".join(chara_values)

        lstinfos_dict = {item["name"]: item for item in lstinfos}
        lstinfos = [lstinfos_dict[k] for k in self.original_lstinfo_order]

        blockdata_s, blockdata_l = msg_pack({"lstInfo": lstinfos})
        ipack = struct.Struct("i")

        data_chunks = [
            ipack.pack(blockdata_l),
            blockdata_s,
            struct.pack("q", len(chara_values)),
            chara_values,
        ]
        return b"".join(data_chunks)

    def save(self, filename):
        data = bytes(self)
        with open(filename, "bw+") as f:
            f.write(data)

    def save_json(self, filename, include_image=False):
        data = {}
        header_data = self._make_dict_header()
        data.update(header_data)

        versions = {}
        for v in self.blockdata:
            data.update({v: getattr(self, v).jsonalizable()})
            versions[v] = getattr(self, v).version
        data["blockdata_versions"] = versions

        with open(filename, "w+") as f:
            json.dump(data, f, indent=2, default=bin_to_str)

    def _make_dict_header(self, **kwargs):
        data = {
            "product_no": self.product_no,
            "header": self.header.decode("utf-8"),
            "version": self.version.decode("utf-8"),
            "blockdata": self.blockdata,
        }
        if "include_image" in kwargs and kwargs["include_image"]:
            if self.image:
                data.update({"image": base64.b64encode(self.image).decode("ascii")})
            data.update({"face_image": base64.b64encode(self.face_image).decode("ascii")})
        return data

    def __str__(self):
        header = self.header.decode("utf-8")
        name = "{} {} ( {} )".format(
            self["Parameter"]["lastname"],
            self["Parameter"]["firstname"],
            self["Parameter"]["nickname"],
        )
        return "{}, {}".format(header, name)

    def __getitem__(self, key):
        if key in self.blockdata:
            return getattr(self, key)
        else:
            raise ValueError("no such blockdata.")

    def __setitem__(self, key, value):
        if key in self.blockdata:
            return setattr(self, key, value)
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

    def __setitem__(self, key, value):
        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]

    def prettify(self):
        print(self.__str__())

    def __str__(self):
        return json.dumps(self.jsonalizable(), indent=2, default=bin_to_str)


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

        if version == "0.0.0":
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

        # エモクリのキャラデータはこのバージョン
        elif version == "0.0.1":
            data_stream = io.BytesIO(data)
            self.data = {
                "clothes": msg_unpack(load_length(data_stream, "i")),
                "accessory": msg_unpack(load_length(data_stream, "i")),
            }

    def serialize(self):
        if self.version == "0.0.0":
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
            serialized_all, _ = msg_pack(data)

        elif self.version == "0.0.1":
            data = []
            pack = struct.Struct("i")
            serialized, length = msg_pack(self.data["clothes"])
            data.extend([pack.pack(length), serialized])
            serialized, length = msg_pack(self.data["accessory"])
            data.extend([pack.pack(length), serialized])
            serialized_all = b"".join(data)

        return serialized_all, self.name, self.version


class Parameter(BlockData):
    def __init__(self, data, version):
        super().__init__(name="Parameter", data=data, version=version)


class Status(BlockData):
    def __init__(self, data, version):
        super().__init__(name="Status", data=data, version=version)


class About(BlockData):
    def __init__(self, data, version):
        super().__init__(name="About", data=data, version=version)


class KKEx(BlockData):
    NESTED_UNPACK = True
    NESTED_KEYS = [
        ["Accessory_States", 1, "CoordinateData"],
        ["Additional_Card_Info", 1, "CardInfo"],
        ["Additional_Card_Info", 1, "CoordinateInfo"],
        ["KCOX", 1, "Overlays"],
        ["KKABMPlugin.ABMData", 1, "boneData"],  # ExtType 99
        ["KSOX", 1, "Lookup"],
        ["MigrationHelper", 1, "Info"],
        ["com.deathweasel.bepinex.clothingunlocker", 1, "ClothingUnlocked"],
        ["com.deathweasel.bepinex.dynamicboneeditor", 1, "AccessoryDynamicBoneData"],
        ["com.deathweasel.bepinex.hairaccessorycustomizer", 1, "HairAccessories"],
        ["com.deathweasel.bepinex.materialeditor", 1, "MaterialColorPropertyList"],
        ["com.deathweasel.bepinex.materialeditor", 1, "MaterialFloatPropertyList"],
        ["com.deathweasel.bepinex.materialeditor", 1, "MaterialShaderList"],
        ["com.deathweasel.bepinex.materialeditor", 1, "MaterialTexturePropertyList"],
        ["com.deathweasel.bepinex.materialeditor", 1, "RendererPropertyList"],
        ["com.deathweasel.bepinex.materialeditor", 1, "TextureDictionary"],
        ["com.deathweasel.bepinex.pushup", 1, "Pushup_BodyData"],
        ["com.deathweasel.bepinex.pushup", 1, "Pushup_BraData"],
        ["com.deathweasel.bepinex.pushup", 1, "Pushup_TopData"],
        ["com.jim60105.kk.charaoverlaysbasedoncoordinate", 1, "IrisDisplaySideList"],
        ["com.snw.bepinex.breastphysicscontroller", 1, "DynamicBoneParameter"],  # ExtType 99
        ["madevil.kk.ass", 1, "CharaTriggerInfo"],
        ["madevil.kk.ass", 1, "CharaVirtualGroupInfo"],
        ["madevil.kk.ass", 1, "CharaVirtualGroupNames"],
        ["madevil.kk.ass", 1, "TriggerGroupList"],
        ["madevil.kk.ass", 1, "TriggerPropertyList"],
        ["madevil.kk.ca", 1, "AAAPKExtdata"],
        ["madevil.kk.ca", 1, "AccStateSyncExtdata"],
        ["madevil.kk.ca", 1, "DynamicBoneEditorExtdata"],
        ["madevil.kk.ca", 1, "HairAccessoryCustomizerExtdata"],
        ["madevil.kk.ca", 1, "MaterialEditorExtdata"],
        ["madevil.kk.ca", 1, "MoreAccessoriesExtdata"],
        ["madevil.kk.ca", 1, "ResolutionInfoExtdata"],
        ["madevil.kk.ca", 1, "TextureContainer"],
        ["marco.authordata", 1, "Authors"],  # ExtType 99
        ["orange.spork.advikplugin", 1, "ResizeChainAdjustments"],
    ]
    LZ4_UNPACK = False
    LZ4_COMPRESSED_KEYS = [
        ["KKABMPlugin.ABMData", 1, "boneData"],
        ["com.deathweasel.bepinex.breastphysicscontroller", 1, "DynamicBoneParameter"],
        ["marco.authordata", 1, "Authors"],
    ]

    def __init__(self, data, version, unpack_nested_kkex=False):
        super().__init__(name="KKEx", data=data, version=version)
        if self.NESTED_UNPACK:
            for keys in self.NESTED_KEYS:
                if self._exists_path(self.data, keys):
                    k1, k2, k3 = keys
                    self.data[k1][k2][k3] = msg_unpack(self.data[k1][k2][k3])

                    # Check if the data is an ExtType with code 99.
                    # This format is used for LZ4 compressed data.
                    if self.LZ4_UNPACK and isinstance(self.data[k1][k2][k3], msgpack.ExtType) and self.data[k1][k2][k3].code == 99 and keys in self.LZ4_COMPRESSED_KEYS:
                        data = self.data[k1][k2][k3].data

                        uncompressed_length = msg_unpack(data[:5])
                        lz4_data = lz4.block.decompress(data[5:], uncompressed_size=uncompressed_length)
                        decompressed = msg_unpack(lz4_data)

                        self.data[k1][k2][k3] = decompressed

    def serialize(self):
        data = copy.deepcopy(self.data)
        if self.NESTED_UNPACK:
            for keys in self.NESTED_KEYS:
                if self._exists_path(data, keys):
                    k1, k2, k3 = keys
                    data[k1][k2][k3], msg_length = msg_pack(data[k1][k2][k3])

                    if self.LZ4_UNPACK and keys in self.LZ4_COMPRESSED_KEYS and msg_length > 64:
                        # By default, data of 64 bytes or less will not be compressed.
                        # ref: https://github.com/MessagePack-CSharp/MessagePack-CSharp/blob/e9ba7483fe45b4b1d133d6c3a0bf0529e212522f/src/MessagePack/MessagePackSerializerOptions.cs#L86-L94
                        compressed_data = lz4.block.compress(data[k1][k2][k3], store_size=False, mode="fast", acceleration=1)
                        compressed_data = b"\xd2" + struct.pack(">i", msg_length) + compressed_data
                        data[k1][k2][k3], _ = msg_pack(msgpack.ExtType(99, compressed_data))

                    # ext8 or ext16
                    if data[k1][k2][k3][0] == 0xC7 or data[k1][k2][k3][0] == 0xC8:
                        data[k1][k2][k3] = self._to_ext32(data[k1][k2][k3])

        data, _ = msg_pack_kkex(data)
        return data, self.name, self.version

    def _exists_path(self, obj, path):
        current = obj
        for key in path:
            try:
                current = current[key]
            except (KeyError, IndexError, TypeError):
                return False
        if current is None:
            return False
        return True

    def _to_ext32(self, buf):
        tag = buf[0]
        # ext8
        if tag == 0xC7:
            # buf = [0xC7][len:1][type:1][data...]
            length = buf[1]
            typ = buf[2]
            data = buf[3:]
        # ext16
        elif tag == 0xC8:
            # buf = [0xC8][len:2][type:1][data...]
            length = struct.unpack(">H", buf[1:3])[0]
            typ = buf[3]
            data = buf[4:]
        else:
            return buf

        # ext32 header: 0xC9 + 4‑byte BE length + 1‑byte type
        new_header = b"\xc9" + struct.pack(">I", length) + bytes((typ,))
        return new_header + data


class UnknownBlockData(BlockData):
    def __init__(self, name, data, version):
        self.data = data
        self.name = name
        self.version = version

    def serialize(self):
        return self.data, self.name, self.version

    def __getitem__(self, key):
        raise ValueError

    def __setitem__(self, key, value):
        raise ValueError

    def prettify(self):
        return self.data
