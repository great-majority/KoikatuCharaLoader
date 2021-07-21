# -*- coding:utf-8 -*-

import io
import json
import struct

from kkloader.funcs import get_png, load_length, load_string, load_type


class EmocreMapData:
    def __init__(self):
        pass

    @staticmethod
    def load(filelike, contains_png=True):
        em = EmocreMapData()

        if isinstance(filelike, str):
            with open(filelike, "br") as f:
                data = f.read()
            data_stream = io.BytesIO(data)

        elif isinstance(filelike, bytes):
            data_stream = io.BytesIO(filelike)

        elif isinstance(filelike, io.BytesIO):
            data_stream = filelike

        else:
            raise ValueError("unsupported input. type:{}".format(type(filelike)))

        em.png_data = None
        if contains_png:
            em.png_data = get_png(data_stream)
        em.product_no = load_type(data_stream, "i")
        em.header = load_length(data_stream, "b")
        em.version = load_length(data_stream, "b")
        em.userid = load_length(data_stream, "b")
        em.dataid = load_length(data_stream, "b")

        length = load_type(data_stream, "i")
        em.packages = []
        for i in range(length):
            em.packages.append(load_type(data_stream, "i"))
        em.name = load_length(data_stream, "b")
        em.language = load_type(data_stream, "i")
        if "0.0.5.2" < em.version.decode():
            em.objects_num = load_type(data_stream, "i")
            em.map_scene = load_type(data_stream, "b")

        em.nodes = []
        length = load_type(data_stream, "i")
        for i in range(length):
            if "0.0.5.2" > em.version.decode():
                load_type(data_stream, "i")
            nodetype = load_type(data_stream, "i")
            em.nodes.append(Node(data_stream, em.version, nodetype=nodetype))

        em.camera_version = load_length(data_stream, "b")
        em.camera_pos = json.loads(load_length(data_stream, "b"))
        em.camera_rot = json.loads(load_length(data_stream, "b"))
        em.camera_dist = load_type(data_stream, "f")
        em.camera_parse = load_type(data_stream, "f")
        em.graphic_size = load_type(data_stream, "f")

        em.light_color = json.loads(load_length(data_stream, "b"))
        em.light_intensity = load_type(data_stream, "f")
        em.light_rot0 = load_type(data_stream, "f")
        em.light_rot1 = load_type(data_stream, "f")
        em.shadow = load_type(data_stream, "b")

        em.map_no = load_type(data_stream, "i")
        em.map_type = load_type(data_stream, "i")

        return em

    def __bytes__(self):
        data = io.BytesIO()
        if self.png_data:
            data.write(self.png_data)
        write_type(data, self.product_no, "i")
        write_string(data, self.header)
        write_string(data, self.version)
        write_string(data, self.userid)
        write_string(data, self.dataid)
        write_type(data, len(self.packages), "i")
        for i in self.packages:
            write_type(data, i, "i")
        write_string(data, self.name)
        write_type(data, self.language, "i")
        if hasattr(self, "objects_num"):
            write_type(data, self.objects_num, "i")
            write_type(data, self.map_scene, "b")
        write_type(data, len(self.nodes), "i")
        for i in self.nodes:
            if "0.0.5.2" > self.version.decode():
                write_type(data, -1, "i")
            write_type(data, i.nodetype, "i")
            i.serialize(data)

        write_string(data, self.camera_version)
        write_json(data, self.camera_pos)
        write_json(data, self.camera_rot)
        write_type(data, self.camera_dist, "f")
        write_type(data, self.camera_parse, "f")
        write_type(data, self.graphic_size, "f")

        write_json(data, self.light_color)
        write_type(data, self.light_intensity, "f")
        write_type(data, self.light_rot0, "f")
        write_type(data, self.light_rot1, "f")
        write_type(data, self.shadow, "b")

        write_type(data, self.map_no, "i")
        write_type(data, self.map_type, "i")

        data.seek(0)
        return data.read()

    def save(self, filename):
        data = self.__bytes__()
        with open(filename, "bw+") as f:
            f.write(data)


class Quantity:
    def __init__(self, data_stream):
        self.pos = json.loads(load_length(data_stream, "b"))
        self.angle = json.loads(load_length(data_stream, "b"))
        self.scale = json.loads(load_length(data_stream, "b"))

    def serialize(self, datas):
        write_json(datas, self.pos)
        write_json(datas, self.angle)
        write_json(datas, self.scale)


class Node:
    def __init__(self, data_stream, version, nodetype=None, skip=False):
        self.nodetype = nodetype
        self.dickey = load_type(data_stream, "i")
        self.quantity = Quantity(data_stream)
        if not skip:
            self.treestate = load_type(data_stream, "i")
            self.visible = load_type(data_stream, "b")

        if nodetype == 1:
            self.package = load_type(data_stream, "i")
            self.no = load_type(data_stream, "i")
            self.animspeed = load_type(data_stream, "f")
            self.colors = []
            for i in range(8):
                self.colors.append(json.loads(load_length(data_stream, "b")))
            self.patterns = []
            for i in range(3):
                pattern = {}
                pattern["key"] = load_type(data_stream, "i")
                pattern["clamp"] = load_type(data_stream, "b")
                pattern["uv"] = json.loads(load_length(data_stream, "b"))
                pattern["rot"] = load_type(data_stream, "f")
                self.patterns.append(pattern)
            self.alpha = load_type(data_stream, "f")
            self.linecolor = json.loads(load_length(data_stream, "b"))
            self.linewidth = load_type(data_stream, "f")
            self.emissioncolor = json.loads(load_length(data_stream, "b"))
            self.emissionpower = load_type(data_stream, "f")
            self.lightcancel = load_type(data_stream, "f")
            if "0.0.3" < version.decode():
                self.piller = Node(data_stream, version, skip=True)
            if "0.0.5.3" < version.decode():
                self.sielding = load_type(data_stream, "b")
            self.nodes = []
            length = load_type(data_stream, "i")
            for i in range(length):
                child_nodetype = load_type(data_stream, "i")
                self.nodes.append(Node(data_stream, version, child_nodetype))

        elif nodetype == 3:
            self.name = load_string(data_stream)
            self.nodes = []
            length = load_type(data_stream, "i")
            for i in range(length):
                child_nodetype = load_type(data_stream, "i")
                self.nodes.append(Node(data_stream, version, child_nodetype))

        elif nodetype == 4:
            self.name = load_length(data_stream, "b")
            self.center = json.loads(load_length(data_stream, "b"))
            self.size = json.loads(load_length(data_stream, "b"))
            self.nodes = []
            length = load_type(data_stream, "i")
            for i in range(length):
                child_nodetype = load_type(data_stream, "i")
                self.nodes.append(Node(data_stream, version, child_nodetype))

    def serialize(self, datas):
        write_type(datas, self.dickey, "i")
        self.quantity.serialize(datas)
        if hasattr(self, "treestate"):
            write_type(datas, self.treestate, "i")
            write_type(datas, self.visible, "b")

        if self.nodetype == 1:
            write_type(datas, self.package, "i")
            write_type(datas, self.no, "i")
            write_type(datas, self.animspeed, "f")
            for i in self.colors:
                write_json(datas, i)
            for i in self.patterns:
                write_type(datas, i["key"], "i")
                write_type(datas, i["clamp"], "b")
                write_json(datas, i["uv"])
                write_type(datas, i["rot"], "f")
            write_type(datas, self.alpha, "f")
            write_json(datas, self.linecolor)
            write_type(datas, self.linewidth, "f")
            write_json(datas, self.emissioncolor)
            write_type(datas, self.emissionpower, "f")
            write_type(datas, self.lightcancel, "f")
            if hasattr(self, "piller"):
                self.piller.serialize(datas)
            if hasattr(self, "sielding"):
                write_type(datas, self.sielding, "b")
            write_type(datas, len(self.nodes), "i")
            for i in self.nodes:
                write_type(datas, i.nodetype, "i")
                i.serialize(datas)

        elif self.nodetype == 3:
            write_string(datas, self.name)
            write_type(datas, len(self.nodes), "i")
            for i in self.nodes:
                write_type(datas, i.nodetype, "i")
                i.serialize(datas)

        elif self.nodetype == 4:
            write_string(datas, self.name)
            write_json(datas, self.center)
            write_json(datas, self.size)
            write_type(datas, len(self.nodes), "i")
            for i in self.nodes:
                write_type(datas, i.nodetype, "i")
                i.serialize(datas)


def write_json(datas, value):
    converted = json.dumps(value, separators=(",", ":")).encode()
    write_string(datas, converted)


def write_type(data_stream, value, format):
    data_stream.write(struct.pack(format, value))


def write_string(datas, value):
    datas.write(struct.pack("b", len(value)))
    datas.write(value)
