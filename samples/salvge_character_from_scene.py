#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import struct
from funcs import load_length, load_type, msg_pack, msg_unpack, get_png_length
from KoikatuCharaData import KoikatuCharaData
import io
import json
import base64
import copy

def search_characters_from_scene(filename):
    data = None
    with open(filename, "br") as f:
        data = f.read()
    
    charas = []
    idx = 0
    while True:
        idx = data.find(b"\x64\x00\x00\x00\x12\xE3\x80\x90\x4B\x6F\x69\x4B\x61\x74\x75\x43\x68\x61\x72\x61\xE3\x80", idx)
        if idx == -1:
            break
        data_stream = io.BytesIO(data[idx:])
        chara = KoikatuCharaData.load(data_stream)
        charas.append(chara)
        idx += 1
    return charas

def main():
    charas = search_characters_from_scene("./datas/kk_scene.png")
    for i,c in enumerate(charas):
        print(c)
        # use face png data instead of png data.
        c.png_data = copy.deepcopy(c.face_png_data)
        c.save("./datas/{}.png".format(i))

if __name__=="__main__":
    main()