#!/usr/bin/env python
# -*- coding:utf-8 -*-

import copy
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from kkloader.EmocreCharaData import EmocreCharaData  # noqa
from kkloader.KoikatuCharaData import Coordinate, KoikatuCharaData  # noqa


def main():
    ec = EmocreCharaData.load("./data/ec_chara.png")
    kk = KoikatuCharaData()

    kk.png_data = ec.png_data
    kk.face_png_data = ec.png_data
    kk.product_no = 100
    kk.header = "【KoiKatuChara】".encode("utf-8")
    kk.version = "0.0.0".encode("ascii")
    kk.blockdata = {
        "lstInfo": [
            {"name": "Custom", "version": "0.0.0"},
            {"name": "Coordinate", "version": "0.0.0"},
            {"name": "Parameter", "version": "0.0.5"},
            {"name": "Status", "version": "0.0.0"},
        ]
    }

    kk.Custom = copy.deepcopy(ec.Custom)
    kk.Coordinate = Coordinate()
    kk.Parameter = copy.deepcopy(ec.Parameter)
    kk.Status = copy.deepcopy(ec.Status)

    kk.Custom.face["version"] = "0.0.2"
    kk.Custom.face["pupilHeight"] *= 1.08
    kk.Custom.face["hlUpY"] = (kk.Custom.face["hlUpY"] - 0.25) * 2
    del kk.Custom.face["hlUpX"]
    del kk.Custom.face["hlDownX"]
    del kk.Custom.face["hlUpScale"]
    del kk.Custom.face["hlDownScale"]
    kk.Custom.body["version"] = "0.0.2"
    kk.Custom.hair["version"] = "0.0.4"

    ec.Coordinate.clothes["hideBraOpt"] = [False, False]
    ec.Coordinate.clothes["hideShortsOpt"] = [False, False]
    for i, p in enumerate(ec.Coordinate.clothes["parts"]):
        a = {
            "emblemeId": p["emblemeId"][0],
            "emblemeId2": p["emblemeId"][1],
        }
        ec.Coordinate.clothes["parts"][i].update(a)
    ec.Coordinate.clothes["parts"].append(ec.Coordinate.clothes["parts"][-1])
    for i, a in enumerate(ec.Coordinate.accessory["parts"]):
        del ec.Coordinate.accessory["parts"][i]["hideTiming"]
    makeup = copy.deepcopy(ec.Custom.face["baseMakeup"])
    kk.Coordinate.coordinates = [
        {
            "clothes": ec.Coordinate.clothes,
            "accessory": ec.Coordinate.accessory,
            "enableMakeup": False,
            "makeup": makeup,
        }
    ] * 7

    kk.Parameter.parameter["version"] = "0.0.5"
    kk.Parameter.parameter["lastname"] = " "
    kk.Parameter.parameter["firstname"] = ec.Parameter.parameter["fullname"]
    kk.Parameter.parameter["nickname"] = " "
    kk.Parameter.parameter["callType"] = -1
    kk.Parameter.parameter["clubActivities"] = 0
    kk.Parameter.parameter["weakPoint"] = 0
    items = [
        "animal",
        "eat",
        "cook",
        "exercise",
        "study",
        "fashionable",
        "blackCoffee",
        "spicy",
        "sweet",
    ]
    kk.Parameter.parameter["awnser"] = dict.fromkeys(items, True)
    items = ["kiss", "aibu", "anal", "massage", "notCondom"]
    kk.Parameter.parameter["denial"] = dict.fromkeys(items, False)
    items = [
        "hinnyo",
        "harapeko",
        "donkan",
        "choroi",
        "bitch",
        "mutturi",
        "dokusyo",
        "ongaku",
        "kappatu",
        "ukemi",
        "friendly",
        "kireizuki",
        "taida",
        "sinsyutu",
        "hitori",
        "undo",
        "majime",
        "likeGirls",
    ]
    kk.Parameter.parameter["attribute"] = dict.fromkeys(items, True)
    kk.Parameter.parameter["aggressive"] = 0
    kk.Parameter.parameter["diligence"] = 0
    kk.Parameter.parameter["kindness"] = 0
    del kk.Parameter.parameter["fullname"]
    kk.Parameter.parameter["personality"] = 0

    kk.Status.status["version"] = "0.0.0"
    kk.Status.status["clothesState"] = b"\x00" * 9
    kk.Status.status["eyesBlink"] = False
    kk.Status.status["mouthPtn"] = 1
    kk.Status.status["mouthOpenMax"] = 0
    kk.Status.status["mouthFixed"] = True
    kk.Status.status["eyesLookPtn"] = 1
    kk.Status.status["neckLookPtn"] = 3
    kk.Status.status["visibleSonAlways"] = False
    del kk.Status.status["mouthOpenMin"]
    del kk.Status.status["enableSonDirection"]
    del kk.Status.status["sonDirectionX"]
    del kk.Status.status["sonDirectionY"]
    kk.Status.status["coordinateType"] = 4
    kk.Status.status["backCoordinateType"] = 0
    kk.Status.status["shoesType"] = 1

    kk.save("./data/converted_ec_chara.png")


if __name__ == "__main__":
    main()
