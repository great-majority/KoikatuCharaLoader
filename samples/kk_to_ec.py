#!/usr/bin/env python
# -*- coding:utf-8 -*-

import copy
import os
import sys
import uuid

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from kkloader.EmocreCharaData import EmocreCharaData  # noqa
from kkloader.KoikatuCharaData import Coordinate, KoikatuCharaData  # noqa


def main():
    kk = KoikatuCharaData.load("./data/kk_chara.png")
    ec = EmocreCharaData()

    ec.image = kk.image
    ec.product_no = 200
    ec.header = "【EroMakeChara】".encode("utf-8")
    ec.version = "0.0.1".encode("ascii")
    ec.language = 0
    ec.userid = str(uuid.uuid4()).encode("ascii")
    ec.dataid = str(uuid.uuid4()).encode("ascii")
    ec.packages = [0]
    ec.blockdata = copy.deepcopy(kk.blockdata)

    ec.Custom = copy.deepcopy(kk.Custom)
    ec.Coordinate = Coordinate(data=None, version="0.0.1")
    ec.Coordinate.data = {"clothes": None, "accessory": None}
    ec.Parameter = copy.deepcopy(kk.Parameter)
    ec.Status = copy.deepcopy(kk.Status)

    ec.Custom.version = "0.0.0"
    ec.Coordinate.version = "0.0.1"
    ec.Parameter.version = "0.0.0"
    ec.Status.version = "0.0.1"

    ec.Custom["face"]["version"] = "0.0.1"
    ec.Custom["face"]["pupilHeight"] *= 0.92
    ec.Custom["face"]["hlUpX"] = 0.5
    ec.Custom["face"]["hlDownX"] = 0.5
    ec.Custom["face"]["hlDownY"] = 0.75
    ec.Custom["face"]["hlUpY"] = (ec.Custom["face"]["hlUpY"] / 2) + 0.25
    ec.Custom["face"]["hlUpScale"] = 0.5
    ec.Custom["face"]["hlDownScale"] = 0.5
    ec.Custom["body"]["version"] = "0.0.0"
    ec.Custom["body"]["typeBone"] = 0
    ec.Custom["hair"]["version"] = "0.0.1"

    for i, h in enumerate(ec.Custom["hair"]["parts"]):
        h["noShake"] = False
        ec.Custom["hair"]["parts"][i] = h

    ec.Coordinate["clothes"] = kk.Coordinate[0]["clothes"]
    del ec.Coordinate["clothes"]["parts"][-2]
    del ec.Coordinate["clothes"]["hideBraOpt"]
    del ec.Coordinate["clothes"]["hideShortsOpt"]
    for i, p in enumerate(ec.Coordinate["clothes"]["parts"]):
        if "emblemeId2" in p:
            p["emblemeId"] = [p["emblemeId"], p["emblemeId2"]]
            del p["emblemeId2"]
        else:
            p["emblemeId"] = [p["emblemeId"], 0]
        p["hideOpt"] = [False, False]
        p["sleevesType"] = 0
        ec.Coordinate["clothes"]["parts"][i] = p
    ec.Coordinate["accessory"] = kk.Coordinate[0]["accessory"]
    for i, a in enumerate(ec.Coordinate["accessory"]["parts"]):
        ec.Coordinate["accessory"]["parts"][i]["hideTiming"] = 1
        ec.Coordinate["accessory"]["parts"][i]["noShake"] = False

    ec.Parameter["version"] = "0.0.0"
    del ec.Parameter["lastname"]
    del ec.Parameter["firstname"]
    del ec.Parameter["nickname"]
    del ec.Parameter["callType"]
    del ec.Parameter["clubActivities"]
    del ec.Parameter["weakPoint"]
    del ec.Parameter["awnser"]  # this is not my typo
    del ec.Parameter["denial"]
    del ec.Parameter["attribute"]
    del ec.Parameter["aggressive"]
    del ec.Parameter["diligence"]
    del ec.Parameter["kindness"]
    name = " ".join(list(map(lambda x: kk.Parameter[x], ["lastname", "firstname"])))
    ec.Parameter["fullname"] = name
    ec.Parameter["personality"] = 0
    ec.Parameter["exType"] = 0

    ec.Status["version"] = "0.0.1"
    ec.Status["clothesState"] = b"\x00" * 8
    ec.Status["eyesBlink"] = True
    ec.Status["mouthPtn"] = 0
    ec.Status["mouthOpenMin"] = 0
    ec.Status["mouthOpenMax"] = 1
    ec.Status["mouthFixed"] = False
    ec.Status["eyesLookPtn"] = 0
    ec.Status["neckLookPtn"] = 0
    ec.Status["visibleSonAlways"] = True
    ec.Status["enableSonDirection"] = False
    ec.Status["sonDirectionX"] = 0
    ec.Status["sonDirectionY"] = 0
    ec.Status["enableShapeHand"] = [False, False]
    ec.Status["shapeHandPtn"] = [2, 2, [0, 0, 0, 0]]
    ec.Status["shapeHandBlendValue"] = [0, 0]
    del ec.Status["coordinateType"]
    del ec.Status["backCoordinateType"]
    del ec.Status["shoesType"]

    ec.save("./data/converted_kk_chara.png")


if __name__ == "__main__":
    main()
