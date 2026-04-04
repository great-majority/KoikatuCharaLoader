"""Aicomi character data loader and saver."""

import kkloader.KoikatuCharaData
from kkloader.HoneycomeCharaData import Coordinate, Custom, Graphic
from kkloader.KoikatuCharaData import BlockData


class AicomiCharaData(kkloader.KoikatuCharaData):
    """Character data class for Aicomi.

    Extends KoikatuCharaData with Aicomi-specific block types,
    reusing Custom, Coordinate, and Graphic from HoneycomeCharaData.
    """

    def __init__(self) -> None:
        """Initialize an AicomiCharaData instance with Aicomi block modules."""
        self.modules = {
            "Custom": Custom,
            "Coordinate": Coordinate,
            "Parameter": kkloader.kk_Parameter,
            "Status": kkloader.kk_Status,
            "Graphic": Graphic,
            "About": kkloader.kk_About,
            "GameParameter_AC": GameParameter_AC,
            "GameInfo_AC": GameInfo_AC,
        }


class GameParameter_AC(BlockData):
    """Block data for Aicomi game parameters."""

    def __init__(self, data: bytes, version: str) -> None:
        """Initialize a GameParameter_AC block data instance.

        Args:
            data: Raw bytes containing the game parameter data.
            version: The version string of this block.
        """
        super().__init__(name="GameParameter_AC", data=data, version=version)


class GameInfo_AC(BlockData):
    """Block data for Aicomi game info."""

    def __init__(self, data: bytes, version: str) -> None:
        """Initialize a GameInfo_AC block data instance.

        Args:
            data: Raw bytes containing the game info data.
            version: The version string of this block.
        """
        super().__init__(name="GameInfo_AC", data=data, version=version)
