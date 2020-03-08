# -*- coding:utf-8 -*-

import struct
from .funcs import load_length, load_type, msg_pack, msg_unpack, get_png, load_string, write_string
from .KoikatuCharaData import KoikatuCharaData
import io
import json
import base64

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
        
        ks.version = load_string(data_stream)
        ks.school_name = load_string(data_stream)
        ks.emblem = load_type(data_stream, "i")
        ks.opening = load_type(data_stream, "b")
        ks.week = load_type(data_stream, "i")

        ks.player = CharaInfo(data_stream)
        
        for name, fmt in ks.variables_1:
            setattr(ks, name, load_type(data_stream, fmt))

        ks.heroines = []
        for i in range(load_type(data_stream, "i")):
            heroine = HeroineInfo(data_stream)
            ks.heroines.append(heroine)
        
        ks.met_personality = []
        for i in range(load_type(data_stream, "i")):
            ks.met_personality.append(load_type(data_stream, "i"))
        
        ks.clubpoint = load_type(data_stream, "i")

        ks.clubcontents = {}
        for i in range(load_type(data_stream, "i")):
            key = load_type(data_stream, "i")
            clubcontent = []
            for n in range(load_type(data_stream, "i")):
                clubcontent.append(load_type(data_stream, "i"))
            ks.clubcontents[key] = clubcontent
        
        ks.clubcontent_items = []
        for i in range(load_type(data_stream, "i")):
            ks.clubcontent_items.append(load_type(data_stream, "i"))
        
        for name, fmt in ks.variables_2:
            setattr(ks, name, load_type(data_stream, fmt))

        ks.action_controls = []
        for i in range(load_type(data_stream, "i")):
            school_class = load_type(data_stream, "i")
            school_class_idx = load_type(data_stream, "i")
            action_control = {}
            for n in range(load_type(data_stream, "i")):
                action_control[load_type(data_stream, "i")] = load_type(data_stream, "i")
            ks.action_controls.append([school_class, school_class_idx, action_control])
        return ks
    
    def __bytes__(self):
        data_stream = io.BytesIO()
        write_string(data_stream, self.version)
        write_string(data_stream, self.school_name)
        data_stream.write(struct.pack("i", self.emblem))
        data_stream.write(struct.pack("b", self.opening))
        data_stream.write(struct.pack("i", self.week))
        
        self.player.serialize(data_stream)

        for name, fmt in self.variables_1:
            data_stream.write(struct.pack(fmt, getattr(self, name)))
        
        data_stream.write(struct.pack("i", len(self.heroines)))
        for i in self.heroines:
            i.serialize(data_stream)
        
        data_stream.write(struct.pack("i", len(self.met_personality)))
        for i in self.met_personality:
            data_stream.write(struct.pack("i", i))
        
        data_stream.write(struct.pack("i",self.clubpoint))

        data_stream.write(struct.pack("i", len(self.clubcontents)))
        for k in self.clubcontents:
            data_stream.write(struct.pack("i", k))
            data_stream.write(struct.pack("i", len(self.clubcontents[k])))
            for i in self.clubcontents[k]:
                data_stream.write(struct.pack("i", i))
        
        data_stream.write(struct.pack("i", len(self.clubcontent_items)))
        for i in self.clubcontent_items:
            data_stream.write(struct.pack("i", i))
    
        for name, fmt in self.variables_2:
            data_stream.write(struct.pack(fmt, getattr(self, name)))
        
        data_stream.write(struct.pack("i", len(self.action_controls)))
        for i in self.action_controls:
            data_stream.write(struct.pack("i", i[0]))
            data_stream.write(struct.pack("i", i[1]))
            data_stream.write(struct.pack("i", len(i[2])))
            for n in i[2]:
                data_stream.write(struct.pack("i", n))
                data_stream.write(struct.pack("i", i[2][n]))
        
        data_stream.seek(0)
        return data_stream.read()

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