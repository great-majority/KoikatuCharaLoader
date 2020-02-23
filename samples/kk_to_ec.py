#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import os
import uuid
import copy
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from KoikatuCharaData import KoikatuCharaData
from EmocreCharaData import EmocreCharaData, Coordinate

def main():
    kk = KoikatuCharaData.load("./datas/kk_chara.png")
    ec = EmocreCharaData()

    ec.png_data = kk.png_data
    ec.product_no = 200
    ec.header = "【EroMakeChara】".encode("utf-8")
    ec.version = "0.0.1".encode("ascii")
    ec.language = 0
    ec.userid = str(uuid.uuid4()).encode("ascii")
    ec.dataid = str(uuid.uuid4()).encode("ascii")
    ec.tags = [0]
    ec.blockdata = {
        "lstInfo":[
            {
                "name": "Custom",
                "version": "0.0.0"
            },
            {
                "name": "Coordinate",
                "version": "0.0.1"
            },
            {
                "name": "Parameter",
                "version": "0.0.0"
            },
            {
                "name": "Status",
                "version": "0.0.1"
            },
        ]
    }

    ec.Custom = copy.deepcopy(kk.Custom)
    ec.Coordinate = Coordinate()
    ec.Parameter = copy.deepcopy(kk.Parameter)
    ec.Status = copy.deepcopy(kk.Status)

    ec.Custom.face["version"] = "0.0.1"
    ec.Custom.face["pupilHeight"] *= 0.92
    ec.Custom.face["hlUpX"] = 0.5
    ec.Custom.face["hlDownX"] = 0.5
    ec.Custom.face["hlUpY"] = (ec.Custom.face["hlUpY"]/2)+0.25
    ec.Custom.face["hlUpScale"] = 0.5
    ec.Custom.face["hlDownScale"] = 0.5
    ec.Custom.body["version"] = "0.0.0"
    ec.Custom.hair["version"] = "0.0.1"

    ec.Coordinate.clothes = kk.Coordinate.coordinates[0]["clothes"]
    del ec.Coordinate.clothes["parts"][-2]
    del ec.Coordinate.clothes["hideBraOpt"]
    del ec.Coordinate.clothes["hideShortsOpt"]
    for i,p in enumerate(ec.Coordinate.clothes["parts"]):
        p["emblemeId"] = [p["emblemeId"], p["emblemeId2"]]
        del p["emblemeId2"]
        ec.Coordinate.clothes["parts"][i] = p
    ec.Coordinate.accessory = kk.Coordinate.coordinates[0]["accessory"]
    for i,a in enumerate(ec.Coordinate.accessory["parts"]):
        ec.Coordinate.accessory["parts"][i]["hideTiming"] = 1
    
    ec.Parameter.parameter["version"] = "0.0.0"
    del ec.Parameter.parameter["lastname"]
    del ec.Parameter.parameter["firstname"]
    del ec.Parameter.parameter["nickname"]
    del ec.Parameter.parameter["callType"]
    del ec.Parameter.parameter["clubActivities"]
    del ec.Parameter.parameter["weakPoint"]
    del ec.Parameter.parameter["awnser"] # this is not my typo
    del ec.Parameter.parameter["denial"]
    del ec.Parameter.parameter["attribute"]
    del ec.Parameter.parameter["aggressive"]
    del ec.Parameter.parameter["diligence"]
    del ec.Parameter.parameter["kindness"]
    name = " ".join(list(map(lambda x: kk.Parameter.parameter[x], ["lastname", "firstname"])))
    ec.Parameter.parameter["fullname"] = name
    ec.Parameter.parameter["personality"] = 0

    ec.Status.status["version"] = "0.0.1"
    ec.Status.status["clothesState"] = b"\x00"*8
    ec.Status.status["eyesBlink"] = True
    ec.Status.status["mouthPtn"] = 0
    ec.Status.status["mouthOpenMin"] = 0
    ec.Status.status["mouthOpenMax"] = 1
    ec.Status.status["mouthFixed"] = False
    ec.Status.status["eyesLookPtn"] = 0
    ec.Status.status["neckLookPtn"] = 0
    ec.Status.status["visibleSonAlways"] = True
    ec.Status.status["enableSonDirection"] = False
    ec.Status.status["sonDirectionX"] = 0
    ec.Status.status["sonDirectionY"] = 0
    del ec.Status.status["coordinateType"]
    del ec.Status.status["backCoordinateType"]
    del ec.Status.status["shoesType"]

    ec.save("./datas/kk_chara_converted.png")

if __name__ == "__main__":
    main()