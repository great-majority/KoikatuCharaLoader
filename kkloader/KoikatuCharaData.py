import base64
import copy
import io
import json
import os
import struct
from typing import Any, ClassVar, Self

from kkloader.funcs import get_png, load_length, load_type, msg_pack, msg_pack_kkex, msg_unpack

import lz4.block
import msgpack


def _bin_to_str(serial: io.BufferedRandom | bytes) -> str:
    """Convert binary data to a base64-encoded ASCII string.

    This function is used as a default serializer for json.dump() to handle
    binary data that is not natively JSON serializable.

    Args:
        serial: Binary data to convert, either as BufferedRandom or bytes.

    Returns:
        Base64-encoded ASCII string representation of the binary data.

    Raises:
        TypeError: If the input is neither BufferedRandom nor bytes.
    """
    if isinstance(serial, io.BufferedRandom) or isinstance(serial, bytes):
        return base64.b64encode(serial.read() if isinstance(serial, io.BufferedRandom) else serial).decode("ascii")
    else:
        raise TypeError("{} is not JSON serializable".format(serial))


class KoikatuCharaData:
    """Main class for loading and saving Koikatu character data.

    Character files are PNG images with binary data appended after the PNG IEND chunk.
    This class handles deserialization and serialization of the character data format.

    Attributes:
        modules: Dictionary mapping block names to their corresponding classes.
        image: Optional PNG image data extracted from the character file.
        product_no: Product number identifier (e.g., 100 for Koikatu).
        header: Header string (e.g., "【KoiKatuChara】").
        version: Version string (e.g., "0.0.0").
        face_image: Face thumbnail image data.
        blockdata: List of block data names in the character file.
        unknown_blockdata: List of unknown block data names.
        original_lstinfo_order: Order of blocks as they appeared in the index.
        serialized_lstinfo_order: Order of blocks as stored in the payload.
    """

    modules: dict[str, type["BlockData"]]
    image: bytes | None
    product_no: int
    header: bytes
    version: bytes
    face_image: bytes
    blockdata: list[str]
    unknown_blockdata: list[str]
    original_file_path: str | None
    original_lstinfo_order: list[str]
    serialized_lstinfo_order: list[str]

    def __init__(self) -> None:
        """Initialize a new KoikatuCharaData instance with default block modules."""
        self.modules = {
            "Custom": Custom,
            "Coordinate": Coordinate,
            "Parameter": Parameter,
            "Status": Status,
            "About": About,
            "KKEx": KKEx,
        }

    @classmethod
    def load(cls, filelike: str | bytes | io.BytesIO, contains_png: bool = True) -> Self:
        """Load character data from a file, bytes, or BytesIO stream.

        Args:
            filelike: Path to a character file, raw bytes, or BytesIO stream.
            contains_png: Whether the input contains a PNG image header.

        Returns:
            A new KoikatuCharaData instance with loaded character data.

        Raises:
            ValueError: If the input type is not supported.
        """
        kc = cls()
        kc.original_file_path = None

        if isinstance(filelike, str):
            with open(filelike, "br") as f:
                data = f.read()
            data_stream = io.BytesIO(data)
            kc.original_file_path = os.path.abspath(filelike)

        elif isinstance(filelike, bytes):
            data_stream = io.BytesIO(filelike)

        elif isinstance(filelike, io.BytesIO):
            data_stream = filelike

        else:
            raise ValueError("unsupported input. type:{}".format(type(filelike)))

        kc._load_header(data_stream, contains_image=contains_png)
        kc._load_blockdata(data_stream)

        return kc

    def _load_header(self, data: io.BytesIO, *, contains_image: bool = False) -> None:
        """Load header information from the data stream.

        Args:
            data: BytesIO stream positioned at the start of the header.
            contains_image: Whether to extract the PNG image from the stream.
        """
        self.image = None
        if contains_image:
            self.image = get_png(data)

        self.product_no = load_type(data, "i")  # 100
        self.header = load_length(data, "b")  # 【KoiKatuChara】
        self.version = load_length(data, "b")  # 0.0.0
        self.face_image = load_length(data, "i")

    def _load_blockdata(self, data: io.BytesIO) -> None:
        """Load block data from the data stream.

        Args:
            data: BytesIO stream positioned at the start of block data.
        """
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
            block_data = lstinfo_raw[pos : pos + size]

            self.blockdata.append(name)
            if name in self.modules.keys():
                setattr(self, name, self.modules[name](block_data, version))
            else:
                setattr(self, name, UnknownBlockData(name, block_data, version))
                self.unknown_blockdata.append(name)

    def __bytes__(self) -> bytes:
        """Convert the character data to bytes for serialization.

        Returns:
            Binary representation of the character data.
        """
        header_bytes = self._make_bytes_header()
        blockdata_bytes = self._make_bytes_blockdata()
        return header_bytes + blockdata_bytes

    def _make_bytes_header(self) -> bytes:
        """Create the binary header data.

        Returns:
            Binary header including image, product_no, header, version, and face_image.
        """
        ipack = struct.Struct("i")
        bpack = struct.Struct("b")
        data_chunks: list[bytes] = []
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

    def _make_bytes_blockdata(self) -> bytes:
        """Create the binary block data payload.

        Returns:
            Binary block data including lstInfo index and serialized blocks.
        """
        cumsum = 0
        chara_values: list[bytes] = []
        lstinfos: list[dict[str, Any]] = []
        for v in self.serialized_lstinfo_order:
            data, name, version = getattr(self, v).serialize()
            lstinfos.append({"name": name, "version": version, "pos": cumsum, "size": len(data)})
            chara_values.append(data)
            cumsum += len(data)
        chara_values_bytes = b"".join(chara_values)

        lstinfos_dict = {item["name"]: item for item in lstinfos}
        lstinfos = [lstinfos_dict[k] for k in self.original_lstinfo_order]

        blockdata_s, blockdata_l = msg_pack({"lstInfo": lstinfos})
        ipack = struct.Struct("i")

        data_chunks = [
            ipack.pack(blockdata_l),
            blockdata_s,
            struct.pack("q", len(chara_values_bytes)),
            chara_values_bytes,
        ]
        return b"".join(data_chunks)

    def save(self, filename: str) -> None:
        """Save the character data to a file.

        Args:
            filename: Path to the output file.
        """
        data = bytes(self)
        with open(filename, "bw+") as f:
            f.write(data)

    def save_json(self, filename: str, include_image: bool = False) -> None:
        """Save the character data as JSON.

        Args:
            filename: Path to the output JSON file.
            include_image: Whether to include base64-encoded images in the output.
        """
        data: dict[str, Any] = {}
        header_data = self._make_dict_header(include_image=include_image)
        data.update(header_data)

        versions: dict[str, str] = {}
        for v in self.blockdata:
            data.update({v: getattr(self, v).jsonalizable()})
            versions[v] = getattr(self, v).version
        data["blockdata_versions"] = versions

        with open(filename, "w+") as f:
            json.dump(data, f, indent=2, default=_bin_to_str)

    def _make_dict_header(self, *, include_image: bool = False) -> dict[str, Any]:
        """Create a dictionary representation of the header.

        Args:
            include_image: Whether to include base64-encoded images.

        Returns:
            Dictionary containing header information.
        """
        data: dict[str, Any] = {
            "product_no": self.product_no,
            "header": self.header.decode("utf-8"),
            "version": self.version.decode("utf-8"),
            "blockdata": self.blockdata,
        }
        if include_image:
            if self.image:
                data.update({"image": base64.b64encode(self.image).decode("ascii")})
            data.update({"face_image": base64.b64encode(self.face_image).decode("ascii")})
        return data

    def _repr_name(self) -> str:
        """Return the character name used by __repr__.

        Returns:
            Character name text inferred from available Parameter fields.
        """
        parameter = getattr(getattr(self, "Parameter", None), "data", {})
        if not isinstance(parameter, dict):
            return ""

        fullname = str(parameter.get("fullname", "")).strip()
        if fullname:
            return fullname

        lastname = str(parameter.get("lastname", "")).strip()
        firstname = str(parameter.get("firstname", "")).strip()
        nickname = str(parameter.get("nickname", "")).strip()
        name = "{} {}".format(lastname, firstname).strip()
        if nickname:
            return "{} ( {} )".format(name, nickname).strip()
        return name

    def _repr_optional_identifiers(self) -> list[tuple[str, str]]:
        """Return optional identifier fields for __repr__.

        Returns:
            Ordered list of (field_name, value) for identifiers that exist.
        """
        about_data = getattr(getattr(self, "About", None), "data", {})
        if not isinstance(about_data, dict):
            about_data = {}

        sources = {
            "userid": [getattr(self, "userid", None), about_data.get("userID"), about_data.get("userid")],
            "dataid": [getattr(self, "dataid", None), about_data.get("dataID"), about_data.get("dataid")],
        }

        identifiers: list[tuple[str, str]] = []
        for field_name, candidates in sources.items():
            for raw_value in candidates:
                if raw_value is None:
                    continue
                if isinstance(raw_value, bytes):
                    value = raw_value.decode("utf-8", errors="replace").strip()
                else:
                    value = str(raw_value).strip()
                if value == "":
                    continue
                identifiers.append((field_name, value))
                break
        return identifiers

    def __repr__(self) -> str:
        """Return a concise debug representation of the character data."""
        blocks = getattr(self, "blockdata", [])
        if not isinstance(blocks, list):
            blocks = []
        header_raw = getattr(self, "header", None)
        version_raw = getattr(self, "version", None)
        header_text = header_raw.decode("utf-8", errors="replace")
        version_text = version_raw.decode("utf-8", errors="replace")

        fields = [
            f"product_no={getattr(self, 'product_no', None)!r}",
            f"header={header_text!r}",
            f"version={version_text!r}",
            f"name={self._repr_name()!r}",
            f"blocks={blocks!r}",
            f"has_kkex={'KKEx' in blocks}",
            f"original_file_path={getattr(self, 'original_file_path', None)!r}",
        ]
        fields.extend([f"{k}={v!r}" for k, v in self._repr_optional_identifiers()])
        return f"{self.__class__.__name__}({', '.join(fields)})"

    def __getitem__(self, key: str) -> "BlockData":
        """Get a block data by name.

        Args:
            key: Name of the block data to retrieve.

        Returns:
            The requested BlockData instance.

        Raises:
            ValueError: If the block data name does not exist.
        """
        if key in self.blockdata:
            return getattr(self, key)
        else:
            raise ValueError("no such blockdata.")

    def __setitem__(self, key: str, value: "BlockData") -> None:
        """Set a block data by name.

        Args:
            key: Name of the block data to set.
            value: The BlockData instance to assign.

        Raises:
            ValueError: If the block data name does not exist.
        """
        if key in self.blockdata:
            setattr(self, key, value)
        else:
            raise ValueError("no such blockdata.")


class BlockData:
    """Base class for all block data types in character files.

    Block data represents a discrete section of character data such as
    Custom, Coordinate, Parameter, Status, About, or KKEx.

    Attributes:
        name: The name identifier of this block data.
        data: The deserialized MessagePack data.
        version: The version string of this block data.
    """

    name: str
    data: Any
    version: str

    def __init__(self, name: str = "Blockdata", data: bytes | None = None, version: str = "0.0.0") -> None:
        """Initialize a BlockData instance.

        Args:
            name: The name identifier of this block data.
            data: Raw bytes to deserialize via MessagePack, or None.
            version: The version string of this block data.
        """
        self.name = name
        self.data = msg_unpack(data)
        self.version = version

    def serialize(self) -> tuple[bytes, str, str]:
        """Serialize the block data to bytes.

        Returns:
            A tuple of (serialized_data, name, version).
        """
        data, _ = msg_pack(self.data)
        return data, self.name, self.version

    def jsonalizable(self) -> Any:
        """Return a JSON-serializable representation of the data.

        Returns:
            The data in a format suitable for JSON serialization.
        """
        return self.data

    def __getitem__(self, key: str) -> Any:
        """Get an item from the data by key.

        Args:
            key: The key to look up in the data.

        Returns:
            The value associated with the key.
        """
        return self.data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set an item in the data by key.

        Args:
            key: The key to set in the data.
            value: The value to assign.
        """
        self.data[key] = value

    def __delitem__(self, key: str) -> None:
        """Delete an item from the data by key.

        Args:
            key: The key to delete from the data.
        """
        del self.data[key]

    def __repr__(self) -> str:
        """Return a string representation of the block data.

        Returns:
            The string representation.
        """
        return self.__str__()

    def prettify(self) -> None:
        """Print a formatted JSON representation of the data."""
        print(self.__str__())

    def __str__(self) -> str:
        """Return a formatted JSON string of the data.

        Returns:
            JSON-formatted string representation.
        """
        return json.dumps(self.jsonalizable(), indent=2, ensure_ascii=False, default=_bin_to_str)


class Custom(BlockData):
    """Block data for custom character appearance (face, body, hair).

    Attributes:
        fields: List of field names in this block.
    """

    fields: ClassVar[list[str]] = ["face", "body", "hair"]

    def __init__(self, data: bytes, version: str) -> None:
        """Initialize a Custom block data instance.

        Args:
            data: Raw bytes containing the custom data.
            version: The version string of this block.
        """
        self.name = "Custom"
        self.version = version
        self.data: dict[str, Any] = {}
        data_stream = io.BytesIO(data)
        for f in self.fields:
            self.data[f] = msg_unpack(load_length(data_stream, "i"))

    def serialize(self) -> tuple[bytes, str, str]:
        """Serialize the custom data to bytes.

        Returns:
            A tuple of (serialized_data, name, version).
        """
        data: list[bytes] = []
        pack = struct.Struct("i")
        for f in self.fields:
            field_s, length = msg_pack(self.data[f])
            data.append(pack.pack(length))
            data.append(field_s)
        serialized = b"".join(data)
        return serialized, self.name, self.version


class Coordinate(BlockData):
    """Block data for character coordinate (outfit) information.

    Handles clothes, accessories, and makeup data for different versions.
    Version 0.0.0 is used for Koikatu, version 0.0.1 for EmotionCreators.
    """

    def __init__(self, data: bytes | None, version: str) -> None:
        """Initialize a Coordinate block data instance.

        Args:
            data: Raw bytes containing the coordinate data, or None.
            version: The version string (0.0.0 for Koikatu, 0.0.1 for EmotionCreators).
        """
        self.name = "Coordinate"
        self.version = version
        if data is None:
            self.data = None
            return

        if version == "0.0.0":
            self.data: list[dict[str, Any]] | dict[str, Any] | None = []
            for c in msg_unpack(data):
                data_stream = io.BytesIO(c)
                coord = {
                    "clothes": msg_unpack(load_length(data_stream, "i")),
                    "accessory": msg_unpack(load_length(data_stream, "i")),
                    "enableMakeup": bool(load_type(data_stream, "b")),
                    "makeup": msg_unpack(load_length(data_stream, "i")),
                }
                self.data.append(coord)

        # EmotionCreators uses this version
        elif version == "0.0.1":
            data_stream = io.BytesIO(data)
            self.data = {
                "clothes": msg_unpack(load_length(data_stream, "i")),
                "accessory": msg_unpack(load_length(data_stream, "i")),
            }

    def serialize(self) -> tuple[bytes, str, str]:
        """Serialize the coordinate data to bytes.

        Returns:
            A tuple of (serialized_data, name, version).

        Raises:
            ValueError: If the version is not supported.
        """
        serialized_all: bytes
        if self.version == "0.0.0":
            data: list[bytes] = []
            for i in self.data:  # type: ignore[union-attr]
                c: list[bytes] = []
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
            data_list: list[bytes] = []
            pack = struct.Struct("i")
            serialized, length = msg_pack(self.data["clothes"])  # type: ignore[index]
            data_list.extend([pack.pack(length), serialized])
            serialized, length = msg_pack(self.data["accessory"])  # type: ignore[index]
            data_list.extend([pack.pack(length), serialized])
            serialized_all = b"".join(data_list)

        else:
            raise ValueError(f"Unsupported version: {self.version}")

        return serialized_all, self.name, self.version


class Parameter(BlockData):
    """Block data for character parameters (name, personality, etc.)."""

    def __init__(self, data: bytes, version: str) -> None:
        """Initialize a Parameter block data instance.

        Args:
            data: Raw bytes containing the parameter data.
            version: The version string of this block.
        """
        super().__init__(name="Parameter", data=data, version=version)


class Status(BlockData):
    """Block data for character status information."""

    def __init__(self, data: bytes, version: str) -> None:
        """Initialize a Status block data instance.

        Args:
            data: Raw bytes containing the status data.
            version: The version string of this block.
        """
        super().__init__(name="Status", data=data, version=version)


class About(BlockData):
    """Block data for character about/description information."""

    def __init__(self, data: bytes, version: str) -> None:
        """Initialize an About block data instance.

        Args:
            data: Raw bytes containing the about data.
            version: The version string of this block.
        """
        super().__init__(name="About", data=data, version=version)


class KKEx(BlockData):
    """Block data for KKEx (extended mod data).

    Contains nested MessagePack payloads from various mods. Some keys use LZ4 compression.

    Attributes:
        NESTED_UNPACK: Whether to recursively unpack nested MessagePack data.
        NESTED_KEYS: List of paths to nested MessagePack data.
        LZ4_UNPACK: Whether to decompress LZ4-compressed data.
        LZ4_COMPRESSED_KEYS: List of paths that use LZ4 compression.
    """

    NESTED_UNPACK: ClassVar[bool] = True
    NESTED_KEYS: ClassVar[list[list[str | int]]] = [
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
    LZ4_UNPACK: ClassVar[bool] = False
    LZ4_COMPRESSED_KEYS: ClassVar[list[list[str | int]]] = [
        ["KKABMPlugin.ABMData", 1, "boneData"],
        ["com.deathweasel.bepinex.breastphysicscontroller", 1, "DynamicBoneParameter"],
        ["marco.authordata", 1, "Authors"],
    ]

    def __init__(self, data: bytes, version: str) -> None:
        """Initialize a KKEx block data instance.

        Args:
            data: Raw bytes containing the KKEx data.
            version: The version string of this block.
        """
        super().__init__(name="KKEx", data=data, version=version)
        if self.NESTED_UNPACK:
            for keys in self.NESTED_KEYS:
                if self._exists_path(self.data, keys):
                    k1, k2, k3 = keys
                    self.data[k1][k2][k3] = msg_unpack(self.data[k1][k2][k3])

                    # Check if the data is an ExtType with code 99.
                    # This format is used for LZ4 compressed data.
                    if self.LZ4_UNPACK and isinstance(self.data[k1][k2][k3], msgpack.ExtType) and self.data[k1][k2][k3].code == 99 and keys in self.LZ4_COMPRESSED_KEYS:
                        ext_data = self.data[k1][k2][k3].data

                        uncompressed_length = msg_unpack(ext_data[:5])
                        lz4_data = lz4.block.decompress(ext_data[5:], uncompressed_size=uncompressed_length)
                        decompressed = msg_unpack(lz4_data)

                        self.data[k1][k2][k3] = decompressed

    def serialize(self) -> tuple[bytes, str, str]:
        """Serialize the KKEx data to bytes.

        Returns:
            A tuple of (serialized_data, name, version).
        """
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

        serialized_data, _ = msg_pack_kkex(data)
        return serialized_data, self.name, self.version

    def _exists_path(self, obj: Any, path: list[str | int]) -> bool:
        """Check if a nested path exists in the object.

        Args:
            obj: The object to check.
            path: List of keys representing the nested path.

        Returns:
            True if the path exists and is not None, False otherwise.
        """
        current = obj
        for key in path:
            try:
                current = current[key]
            except (KeyError, IndexError, TypeError):
                return False
        if current is None:
            return False
        return True

    def _to_ext32(self, buf: bytes) -> bytes:
        """Convert ext8 or ext16 format to ext32 format.

        Args:
            buf: The buffer containing ext8 or ext16 data.

        Returns:
            The buffer converted to ext32 format, or the original if not ext8/ext16.
        """
        tag = buf[0]
        # ext8
        if tag == 0xC7:
            # buf = [0xC7][len:1][type:1][data...]
            length = buf[1]
            typ = buf[2]
            payload = buf[3:]
        # ext16
        elif tag == 0xC8:
            # buf = [0xC8][len:2][type:1][data...]
            length = struct.unpack(">H", buf[1:3])[0]
            typ = buf[3]
            payload = buf[4:]
        else:
            return buf

        # ext32 header: 0xC9 + 4-byte BE length + 1-byte type
        new_header = b"\xc9" + struct.pack(">I", length) + bytes((typ,))
        return new_header + payload


class UnknownBlockData(BlockData):
    """Block data for unknown/unrecognized block types.

    Stores raw data without deserialization for blocks that are not recognized.
    """

    def __init__(self, name: str, data: bytes, version: str) -> None:
        """Initialize an UnknownBlockData instance.

        Args:
            name: The name identifier of this block data.
            data: Raw bytes (stored without deserialization).
            version: The version string of this block.
        """
        self.data = data
        self.name = name
        self.version = version

    def serialize(self) -> tuple[bytes, str, str]:
        """Serialize the unknown block data.

        Returns:
            A tuple of (raw_data, name, version).
        """
        return self.data, self.name, self.version

    def __getitem__(self, _key: str) -> Any:
        """Not supported for unknown block data.

        Raises:
            ValueError: Always raised as unknown blocks cannot be indexed.
        """
        raise ValueError("Cannot index into unknown block data")

    def __setitem__(self, _key: str, _value: Any) -> None:
        """Not supported for unknown block data.

        Raises:
            ValueError: Always raised as unknown blocks cannot be indexed.
        """
        raise ValueError("Cannot set items in unknown block data")

    def prettify(self) -> None:
        """Print the raw data."""
        print(self.data)
