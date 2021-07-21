# -*- coding:utf-8 -*-

import io

from kkloader.EmocreCharaData import EmocreCharaData
from kkloader.EmocreMapData import EmocreMapData
from kkloader.funcs import get_png, load_length, load_type


class EmocreSceneData:
    def __init__(self):
        pass

    @staticmethod
    def load(filelike):
        es = EmocreSceneData()

        if isinstance(filelike, str):
            with open(filelike, "br") as f:
                data = f.read()
            data_stream = io.BytesIO(data)

        elif isinstance(filelike, bytes):
            data_stream = io.BytesIO(filelike)

        else:
            ValueError("unsupported input. type:{}".format(type(filelike)))

        es.png_data = get_png(data_stream)
        es.product_no = load_type(data_stream, "i")
        es.header = load_length(data_stream, "b")
        es.version = load_length(data_stream, "b")

        es.language = load_type(data_stream, "i")
        es.userid = load_length(data_stream, "b")
        es.dataid = load_length(data_stream, "b")
        es.title = load_length(data_stream, "b")
        es.comment = load_length(data_stream, "b")
        es.defaultbgm = load_type(data_stream, "i")
        es.tags = []
        length = load_type(data_stream, "i")
        for i in range(length):
            es.tags.append(load_type(data_stream, "i"))
        es.males = load_type(data_stream, "i")
        es.females = load_type(data_stream, "i")
        es.isplaying = load_type(data_stream, "b")
        es.uses_adv = load_type(data_stream, "b")
        es.uses_hpart = load_type(data_stream, "b")
        length = load_type(data_stream, "i")
        es.charapackages = []
        for i in range(length):
            es.charapackages.append(load_type(data_stream, "i"))
        length = load_type(data_stream, "i")
        es.mappackages = []
        for i in range(length):
            es.mappackages.append(load_type(data_stream, "i"))
        es.uses_mapset = load_type(data_stream, "b")
        es.mapobjects = load_type(data_stream, "i")

        length = load_type(data_stream, "i")
        es.charas = []
        for i in range(length):
            chara = EmocreCharaData.load(data_stream)
            es.charas.append(chara)

        length = load_type(data_stream, "i")
        es.maps = []
        for i in range(length):
            map = EmocreMapData.load(data_stream, contains_png=False)
            es.maps.append(map)

        return es
