"""Honeycome character data loader and saver."""

import io
import struct
from typing import Any, ClassVar

import kkloader.KoikatuCharaData
from kkloader.funcs import load_length, msg_pack, msg_unpack
from kkloader.KoikatuCharaData import BlockData


class HoneycomeCharaData(kkloader.KoikatuCharaData):
    """Character data class for Honeycome and Honeycome Party.

    Extends KoikatuCharaData with Honeycome-specific block types including
    Custom (face/body only), Coordinate (with hair/nail), Graphic, and
    game-specific parameters.
    """

    def __init__(self) -> None:
        """Initialize a HoneycomeCharaData instance with Honeycome block modules."""
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
    """Block data for Honeycome custom character appearance (face, body only).

    Unlike Koikatu's Custom which includes hair, Honeycome handles hair
    in the Coordinate block.

    Attributes:
        fields: List of field names in this block.
    """

    fields: ClassVar[list[str]] = ["face", "body"]

    def __init__(self, data: bytes, version: str) -> None:
        """Initialize a Honeycome Custom block data instance.

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
    """Block data for Honeycome coordinate (outfit) information.

    Includes clothes, accessories, makeup, hair, and nail data.

    Attributes:
        fields: List of field names in each coordinate.
    """

    fields: ClassVar[list[str]] = [
        "clothes",
        "accessory",
        "makeup",
        "hair",
        "nail",
    ]

    def __init__(self, data: bytes | None, version: str) -> None:
        """Initialize a Honeycome Coordinate block data instance.

        Args:
            data: Raw bytes containing the coordinate data, or None.
            version: The version string of this block.
        """
        self.name = "Coordinate"
        self.version = version
        if data is None:
            self.data = None
            return

        self.data: list[dict[str, Any]] | None = []
        for coordinate_bytes in msg_unpack(data):
            data_stream = io.BytesIO(coordinate_bytes)
            coordinate_dict: dict[str, Any] = {}
            for f in self.fields:
                coordinate_dict[f] = msg_unpack(load_length(data_stream, "i"))
            self.data.append(coordinate_dict)

    def serialize(self) -> tuple[bytes, str, str]:
        """Serialize the coordinate data to bytes.

        Returns:
            A tuple of (serialized_data, name, version).
        """
        data: list[bytes] = []
        for i in self.data:  # type: ignore[union-attr]
            c: list[bytes] = []
            pack = struct.Struct("i")

            for f in self.fields:
                serialized, length = msg_pack(i[f])
                c.extend([pack.pack(length), serialized])

            data.append(b"".join(c))
        serialized_all, _ = msg_pack(data)

        return serialized_all, self.name, self.version


class Graphic(BlockData):
    """Block data for Honeycome graphics settings."""

    def __init__(self, data: bytes, version: str) -> None:
        """Initialize a Graphic block data instance.

        Args:
            data: Raw bytes containing the graphic data.
            version: The version string of this block.
        """
        super().__init__(name="Graphic", data=data, version=version)


class GameParameter_HCP(BlockData):
    """Block data for Honeycome Party game parameters."""

    def __init__(self, data: bytes, version: str) -> None:
        """Initialize a GameParameter_HCP block data instance.

        Args:
            data: Raw bytes containing the game parameter data.
            version: The version string of this block.
        """
        super().__init__(name="GameParameter_HCP", data=data, version=version)


class GameInfo_HCP(BlockData):
    """Block data for Honeycome Party game info."""

    def __init__(self, data: bytes, version: str) -> None:
        """Initialize a GameInfo_HCP block data instance.

        Args:
            data: Raw bytes containing the game info data.
            version: The version string of this block.
        """
        super().__init__(name="GameInfo_HCP", data=data, version=version)


class GameParameter_HC(BlockData):
    """Block data for Honeycome game parameters."""

    def __init__(self, data: bytes, version: str) -> None:
        """Initialize a GameParameter_HC block data instance.

        Args:
            data: Raw bytes containing the game parameter data.
            version: The version string of this block.
        """
        super().__init__(name="GameParameter_HC", data=data, version=version)


class GameInfo_HC(BlockData):
    """Block data for Honeycome game info."""

    def __init__(self, data: bytes, version: str) -> None:
        """Initialize a GameInfo_HC block data instance.

        Args:
            data: Raw bytes containing the game info data.
            version: The version string of this block.
        """
        super().__init__(name="GameInfo_HC", data=data, version=version)
