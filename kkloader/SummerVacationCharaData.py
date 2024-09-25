import kkloader.KoikatuCharaData
from kkloader.HoneycomeCharaData import Coordinate, Custom, Graphic
from kkloader.KoikatuCharaData import BlockData


class SummerVacationCharaData(kkloader.KoikatuCharaData):
    def __init__(self):
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
    def __init__(self, data, version):
        super().__init__(name="GameParameter_SV", data=data, version=version)


class GameInfo_SV(BlockData):
    def __init__(self, data, version):
        super().__init__(name="GameInfo_SV", data=data, version=version)
