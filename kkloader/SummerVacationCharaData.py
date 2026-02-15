"""SummerVacationScramble character data loader and saver."""

import kkloader.KoikatuCharaData
from kkloader.HoneycomeCharaData import Coordinate, Custom, Graphic
from kkloader.KoikatuCharaData import BlockData


class SummerVacationCharaData(kkloader.KoikatuCharaData):
    """Character data class for SummerVacationScramble.

    Extends KoikatuCharaData with SummerVacation-specific block types,
    reusing Custom, Coordinate, and Graphic from HoneycomeCharaData.
    """

    def __init__(self) -> None:
        """Initialize a SummerVacationCharaData instance with SummerVacation block modules."""
        self.modules = {
            "Custom": Custom,
            "Coordinate": Coordinate,
            "Parameter": kkloader.kk_Parameter,
            "Status": kkloader.kk_Status,
            "Graphic": Graphic,
            "About": kkloader.kk_About,
            "GameParameter_SV": GameParameter_SV,
            "GameInfo_SV": GameInfo_SV,
        }

class GameParameter_SV(BlockData):
    """Block data for SummerVacationScramble game parameters."""

    def __init__(self, data: bytes, version: str) -> None:
        """Initialize a GameParameter_SV block data instance.

        Args:
            data: Raw bytes containing the game parameter data.
            version: The version string of this block.
        """
        super().__init__(name="GameParameter_SV", data=data, version=version)


class GameInfo_SV(BlockData):
    """Block data for SummerVacationScramble game info."""

    def __init__(self, data: bytes, version: str) -> None:
        """Initialize a GameInfo_SV block data instance.

        Args:
            data: Raw bytes containing the game info data.
            version: The version string of this block.
        """
        super().__init__(name="GameInfo_SV", data=data, version=version)
