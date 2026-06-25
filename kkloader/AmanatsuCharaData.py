"""Amanatsu Location character data loader and saver."""

import io
import struct
from typing import Any

import kkloader.KoikatuCharaData
from kkloader.funcs import load_length, load_type, msg_pack, msg_unpack
from kkloader.HoneycomeCharaData import Custom, Graphic
from kkloader.KoikatuCharaData import BlockData


class AmanatsuCharaData(kkloader.KoikatuCharaData):
    """Character data class for Amanatsu Location (甘夏ろけーしょん).

    Extends KoikatuCharaData with Amanatsu Location-specific block types.
    Reuses Custom and Graphic from HoneycomeCharaData.
    """

    def __init__(self) -> None:
        """Initialize an AmanatsuCharaData instance with Amanatsu Location block modules."""
        self.modules = {
            "Custom": Custom,
            "Coordinate": Coordinate,
            "Parameter": kkloader.kk_Parameter,
            "Status": kkloader.kk_Status,
            "Graphic": Graphic,
            "About": kkloader.kk_About,
            "GameParameter_AL": GameParameter_AL,
            "GameInfo_AL": GameInfo_AL,
            "ThumbParameter": ThumbParameter,
        }


class CoordinateEntry:
    """A single coordinate (outfit) entry with nested lstInfo block structure.

    Each entry has its own header (【ALClothes】), version, and sub-blocks
    (Clothes, Accessory, Hair, FaceMakeup, BodyMakeup, About).
    """

    def __init__(self) -> None:
        """Initialize an empty CoordinateEntry."""
        self.product_no: int = 0
        self.header: bytes = b""
        self.version: bytes = b""
        self.unknown: bytes = b"\x00\x00"
        self.blockdata: list[str] = []
        self.original_lstinfo_order: list[str] = []
        self.serialized_lstinfo_order: list[str] = []

    @classmethod
    def load(cls, raw_bytes: bytes) -> "CoordinateEntry":
        """Load a coordinate entry from raw bytes.

        Args:
            raw_bytes: The raw bytes of a single coordinate entry.

        Returns:
            A CoordinateEntry instance with loaded data.
        """
        entry = cls()
        stream = io.BytesIO(raw_bytes)

        entry.product_no = load_type(stream, "i")
        entry.header = load_length(stream, "b")
        entry.version = load_length(stream, "b")
        entry.unknown = stream.read(2)

        lstinfo_index = msg_unpack(load_length(stream, "i"))
        lstinfo_raw = load_length(stream, "q")

        entry.blockdata = []
        entry.original_lstinfo_order = list(map(lambda x: x["name"], lstinfo_index["lstInfo"]))
        entry.serialized_lstinfo_order = list(map(lambda x: x["name"], sorted(lstinfo_index["lstInfo"], key=lambda x: x["pos"])))

        for i in lstinfo_index["lstInfo"]:
            name = i["name"]
            pos = i["pos"]
            size = i["size"]
            version = i["version"]
            block_data = lstinfo_raw[pos : pos + size]
            entry.blockdata.append(name)
            setattr(entry, name, BlockData(name=name, data=block_data, version=version))

        return entry

    def __bytes__(self) -> bytes:
        """Serialize the coordinate entry to bytes.

        Returns:
            Binary representation of the coordinate entry.
        """
        cumsum = 0
        block_values: list[bytes] = []
        lstinfos: list[dict[str, Any]] = []
        for name in self.serialized_lstinfo_order:
            data, block_name, version = getattr(self, name).serialize()
            lstinfos.append({"name": block_name, "version": version, "pos": cumsum, "size": len(data)})
            block_values.append(data)
            cumsum += len(data)
        block_payload = b"".join(block_values)

        lstinfos_dict = {item["name"]: item for item in lstinfos}
        lstinfos_ordered = [lstinfos_dict[k] for k in self.original_lstinfo_order]

        lstinfo_packed, lstinfo_len = msg_pack({"lstInfo": lstinfos_ordered})

        ipack = struct.Struct("i")
        bpack = struct.Struct("b")
        parts = [
            ipack.pack(self.product_no),
            bpack.pack(len(self.header)),
            self.header,
            bpack.pack(len(self.version)),
            self.version,
            self.unknown,
            ipack.pack(lstinfo_len),
            lstinfo_packed,
            struct.pack("q", len(block_payload)),
            block_payload,
        ]
        return b"".join(parts)

    def jsonalizable(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the coordinate entry.

        Returns:
            Dictionary of sub-block data.
        """
        result: dict[str, Any] = {}
        for name in self.blockdata:
            result[name] = getattr(self, name).jsonalizable()
        return result


class Coordinate(BlockData):
    """Block data for Amanatsu Location coordinate (outfit) information.

    Each coordinate entry is a nested lstInfo-based structure with its own
    header (【ALClothes】) and sub-blocks (Clothes, Accessory, Hair,
    FaceMakeup, BodyMakeup, About).
    """

    def __init__(self, data: bytes | None, version: str) -> None:
        """Initialize an Amanatsu Location Coordinate block data instance.

        Args:
            data: Raw bytes containing the coordinate data, or None.
            version: The version string of this block.
        """
        self.name = "Coordinate"
        self.version = version
        if data is None:
            self.data = None
            return

        self.data: list[CoordinateEntry] | None = []
        for coordinate_bytes in msg_unpack(data):
            self.data.append(CoordinateEntry.load(coordinate_bytes))

    def serialize(self) -> tuple[bytes, str, str]:
        """Serialize the coordinate data to bytes.

        Returns:
            A tuple of (serialized_data, name, version).
        """
        entries: list[bytes] = []
        for entry in self.data:  # type: ignore[union-attr]
            entries.append(bytes(entry))
        serialized, _ = msg_pack(entries)
        return serialized, self.name, self.version

    def jsonalizable(self) -> Any:
        """Return a JSON-serializable representation of the data.

        Returns:
            List of coordinate entry dictionaries.
        """
        if self.data is None:
            return None
        return [entry.jsonalizable() for entry in self.data]


class GameParameter_AL(BlockData):
    """Block data for Amanatsu Location game parameters."""

    def __init__(self, data: bytes, version: str) -> None:
        """Initialize a GameParameter_AL block data instance.

        Args:
            data: Raw bytes containing the game parameter data.
            version: The version string of this block.
        """
        super().__init__(name="GameParameter_AL", data=data, version=version)


class GameInfo_AL(BlockData):
    """Block data for Amanatsu Location game info."""

    def __init__(self, data: bytes, version: str) -> None:
        """Initialize a GameInfo_AL block data instance.

        Args:
            data: Raw bytes containing the game info data.
            version: The version string of this block.
        """
        super().__init__(name="GameInfo_AL", data=data, version=version)


class ThumbParameter(BlockData):
    """Block data for Amanatsu Location thumbnail parameters."""

    def __init__(self, data: bytes, version: str) -> None:
        """Initialize a ThumbParameter block data instance.

        Args:
            data: Raw bytes containing the thumbnail parameter data.
            version: The version string of this block.
        """
        super().__init__(name="ThumbParameter", data=data, version=version)
