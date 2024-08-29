# -*- coding:utf-8 -*-

import io
import struct

from kkloader import KoikatuCharaData
from kkloader.funcs import load_string, load_type, write_string


class KoikatuSaveData:
    variables_1 = [
        ("girlfriends", "i"),
        ("hpeople_cnt", "i"),
        ("org_cnt", "i"),
        ("h_cnt", "i"),
        ("intel", "i"),
        ("physical", "i"),
        ("hentai", "i"),
        ("playtime_calc", "f"),
        ("change_clothtype", "i"),
        ("playtime", "i"),
    ]
    variables_2 = [
        ("staffadd", "i"),
        ("comadd", "i"),
        ("hadd", "f"),
        ("staff", "i"),
        ("point", "i"),
        ("withheroine", "i"),
        ("dateheroine", "i"),
    ]

    def __init__(self):
        pass

    @staticmethod
    def load(filelike):
        ks = KoikatuSaveData()

        if isinstance(filelike, str):
            with open(filelike, "br") as f:
                data = f.read()
            data_stream = io.BytesIO(data)

        elif isinstance(filelike, bytes):
            data_stream = io.BytesIO(filelike)

        elif isinstance(filelike, io.BytesIO):
            data_stream = filelike

        else:
            ValueError("unsupported input. type:{}".format(type(filelike)))

        ks._load_header(data_stream)
        ks._load_player(data_stream)
        ks._load_vars1(data_stream)
        ks._load_heroines(data_stream)
        ks._load_personality(data_stream)
        ks._load_club_data(data_stream)
        ks._load_vars2(data_stream)
        ks._load_action_controls(data_stream)

        return ks

    def __bytes__(self):
        data_stream = io.BytesIO()

        self._serialize_header(data_stream)
        self._serialize_player(data_stream)
        self._serialize_vars1(data_stream)
        self._serialize_heroines(data_stream)
        self._serialize_personality(data_stream)
        self._serialize_club_data(data_stream)
        self._serialize_vars2(data_stream)
        self._serialize_action_controls(data_stream)

        data_stream.seek(0)
        return data_stream.read()

    def _load_header(self, data_stream):
        self.version = load_string(data_stream)
        self.school_name = load_string(data_stream)
        self.emblem = load_type(data_stream, "i")
        self.opening = load_type(data_stream, "b")
        self.week = load_type(data_stream, "i")

    def _serialize_header(self, data_stream):
        write_string(data_stream, self.version)
        write_string(data_stream, self.school_name)
        data_stream.write(struct.pack("i", self.emblem))
        data_stream.write(struct.pack("b", self.opening))
        data_stream.write(struct.pack("i", self.week))

    def _load_player(self, data_stream):
        self.player = CharaInfo(data_stream)

    def _serialize_player(self, data_stream):
        self.player.serialize(data_stream)

    def _load_vars1(self, data_stream):
        for name, fmt in self.variables_1:
            setattr(self, name, load_type(data_stream, fmt))

    def _serialize_vars1(self, data_stream):
        for name, fmt in self.variables_1:
            data_stream.write(struct.pack(fmt, getattr(self, name)))

    def _load_heroines(self, data_stream):
        self.heroines = []
        for i in range(load_type(data_stream, "i")):
            heroine = HeroineInfo(data_stream)
            self.heroines.append(heroine)

    def _serialize_heroines(self, data_stream):
        data_stream.write(struct.pack("i", len(self.heroines)))
        for i in self.heroines:
            i.serialize(data_stream)

    def _load_personality(self, data_stream):
        self.met_personality = []
        for i in range(load_type(data_stream, "i")):
            self.met_personality.append(load_type(data_stream, "i"))

    def _serialize_personality(self, data_stream):
        data_stream.write(struct.pack("i", len(self.met_personality)))
        for i in self.met_personality:
            data_stream.write(struct.pack("i", i))

    def _load_club_data(self, data_stream):
        self.clubpoint = load_type(data_stream, "i")

        self.clubcontents = {}
        for i in range(load_type(data_stream, "i")):
            key = load_type(data_stream, "i")
            clubcontent = []
            for n in range(load_type(data_stream, "i")):
                clubcontent.append(load_type(data_stream, "i"))
            self.clubcontents[key] = clubcontent

        self.clubcontent_items = []
        for i in range(load_type(data_stream, "i")):
            self.clubcontent_items.append(load_type(data_stream, "i"))

    def _serialize_club_data(self, data_stream):
        data_stream.write(struct.pack("i", self.clubpoint))

        data_stream.write(struct.pack("i", len(self.clubcontents)))
        for k in self.clubcontents:
            data_stream.write(struct.pack("i", k))
            data_stream.write(struct.pack("i", len(self.clubcontents[k])))
            for i in self.clubcontents[k]:
                data_stream.write(struct.pack("i", i))

        data_stream.write(struct.pack("i", len(self.clubcontent_items)))
        for i in self.clubcontent_items:
            data_stream.write(struct.pack("i", i))

    def _load_vars2(self, data_stream):
        for name, fmt in self.variables_2:
            setattr(self, name, load_type(data_stream, fmt))

    def _serialize_vars2(self, data_stream):
        for name, fmt in self.variables_2:
            data_stream.write(struct.pack(fmt, getattr(self, name)))

    def _load_action_controls(self, data_stream):
        self.action_controls = []
        for i in range(load_type(data_stream, "i")):
            school_class = load_type(data_stream, "i")
            school_class_idx = load_type(data_stream, "i")
            action_control = []
            for n in range(load_type(data_stream, "i")):
                action_control.append([load_type(data_stream, "i"), load_type(data_stream, "i")])
            self.action_controls.append([school_class, school_class_idx, action_control])

    def _serialize_action_controls(self, data_stream):
        data_stream.write(struct.pack("i", len(self.action_controls)))
        for i in self.action_controls:
            data_stream.write(struct.pack("i", i[0]))
            data_stream.write(struct.pack("i", i[1]))
            data_stream.write(struct.pack("i", len(i[2])))
            for n in i[2]:
                data_stream.write(struct.pack("i", n[0]))
                data_stream.write(struct.pack("i", n[1]))

    def save(self, filename):
        data = bytes(self)
        with open(filename, "bw+") as f:
            f.write(data)


class CharaInfo:
    def __init__(self, data_stream):
        self.chara_class = load_type(data_stream, "i")
        self.class_idx = load_type(data_stream, "i")
        self.chara = KoikatuCharaData.load(data_stream, False)
        self.nametype = load_type(data_stream, "i")
        self.callid = load_type(data_stream, "i")
        self.callname = load_string(data_stream)

    def serialize(self, data_stream):
        data_stream.write(struct.pack("i", self.chara_class))
        data_stream.write(struct.pack("i", self.class_idx))
        data_stream.write(bytes(self.chara))
        data_stream.write(struct.pack("i", self.nametype))
        data_stream.write(struct.pack("i", self.callid))
        write_string(data_stream, self.callname)


class HeroineInfo:
    variables_1 = [
        ("favor", "i"),
        ("lewdness", "i"),
        ("h_cnt", "i"),
        ("is_staff", "b"),
        ("is_girlfriend", "b"),
        ("is_anger", "b"),
        ("fix_chara_id", "i"),
        ("is_taked", "b"),
        ("is_date", "b"),
        ("nickname_talk_cnt", "i"),
        ("myroom_cnt", "i"),
        ("menstruction_start", "i"),
        ("menstruction", "b"),
    ]
    variables_2 = [
        ("is_virgin", "b"),
        ("is_analvirgin", "b"),
        ("kokan_h_cnt", "f"),
        ("anal_h_cnt", "f"),
        ("is_kiss", "b"),
        ("count_nama_insert", "i"),
        ("count_nama_houshi", "i"),
    ]
    variables_3 = [
        ("houshiexp", "f"),
        ("event_afterday", "i"),
        ("is_first_girlfriend", "b"),
        ("intimacy", "i"),
    ]

    def __init__(self, data_stream):
        self.chara_info = CharaInfo(data_stream)

        for name, fmt in self.variables_1:
            setattr(self, name, load_type(data_stream, fmt))

        self.h_exps = []
        for i in range(load_type(data_stream, "i")):
            self.h_exps.append(load_type(data_stream, "f"))

        self.massage_exps = []
        for i in range(load_type(data_stream, "i")):
            self.massage_exps.append(load_type(data_stream, "f"))

        for name, fmt in self.variables_2:
            setattr(self, name, load_type(data_stream, fmt))

        self.talk_events = []
        for i in range(load_type(data_stream, "i")):
            self.talk_events.append(load_type(data_stream, "i"))

        self.talk_temper = data_stream.read(39)
        self.conffessed = load_type(data_stream, "b")

        self.motionspeeds = {}
        for i in range(load_type(data_stream, "i")):
            key = load_string(data_stream)
            value = load_type(data_stream, "f")
            self.motionspeeds[key] = value

        for name, fmt in self.variables_3:
            setattr(self, name, load_type(data_stream, fmt))

    def serialize(self, data_stream):
        self.chara_info.serialize(data_stream)

        for name, fmt in self.variables_1:
            data_stream.write(struct.pack(fmt, getattr(self, name)))

        data_stream.write(struct.pack("i", len(self.h_exps)))
        for i in self.h_exps:
            data_stream.write(struct.pack("f", i))

        data_stream.write(struct.pack("i", len(self.massage_exps)))
        for i in self.massage_exps:
            data_stream.write(struct.pack("f", i))

        for name, fmt in self.variables_2:
            data_stream.write(struct.pack(fmt, getattr(self, name)))

        data_stream.write(struct.pack("i", len(self.talk_events)))
        for i in self.talk_events:
            data_stream.write(struct.pack("i", i))

        data_stream.write(self.talk_temper)
        data_stream.write(struct.pack("b", self.conffessed))

        data_stream.write(struct.pack("i", len(self.motionspeeds)))
        for k in self.motionspeeds:
            write_string(data_stream, k)
            data_stream.write(struct.pack("f", self.motionspeeds[k]))

        for name, fmt in self.variables_3:
            data_stream.write(struct.pack(fmt, getattr(self, name)))
