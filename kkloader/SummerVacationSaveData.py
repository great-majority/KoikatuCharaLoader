import io
import struct

from kkloader import SummerVacationCharaData as svcd
from kkloader.funcs import load_length, msg_pack, msg_unpack

import pandas as pd


class SummerVacationSaveData:
    def __init__(self) -> None:
        pass

    @classmethod
    def _unsigned_int(cls, data_stream):
        return struct.unpack("<I", data_stream.read(4))[0]

    @classmethod
    def _unsigned_int64(cls, data_stream):
        return struct.unpack("<Q", data_stream.read(8))[0]

    @classmethod
    def load(cls, filelike):
        svs = cls()

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

        # Meta information of the save data
        svs.meta = msg_unpack(load_length(data_stream, "<I"))
        # The total data length minus 12 is stored
        svs.data_length = cls._unsigned_int64(data_stream)
        # The number of registered characters
        svs.chara_num = cls._unsigned_int(data_stream)

        svs.chara_details = []
        svs.charas = []
        # Data for each character
        for i in range(svs.chara_num):
            # The length of the data: length of the parameters (and 4 bytes representing that length) + character data length
            cls._unsigned_int(data_stream)
            # Data about relationships between characters
            svs.chara_details.append(msg_unpack(load_length(data_stream, "<I")))
            # Character data
            svs.charas.append(svcd.load(data_stream))

        # Was set to `1`, but the details are unclear
        svs.unknown = cls._unsigned_int(data_stream)
        # The offset position where the player's character data is stored
        svs.player_offset = cls._unsigned_int64(data_stream)

        svs.names = {}
        for c, d in zip(svs.charas, svs.chara_details):
            svs.names[d["charasGameParam"]["Index"]] = f"{c['Parameter']['lastname']} {c['Parameter']['firstname']}"

        return svs

    # Save Data Serialization
    def __bytes__(self):
        ipack = struct.Struct("<I").pack
        qpack = struct.Struct("<Q").pack

        meta_b, meta_i = msg_pack(self.meta)
        meta_i_b = ipack(meta_i)

        chara_byte, player_offset = self._bytes_charas()
        chara_l_b = ipack(len(self.charas))

        # We want to calculate the offset from the start of the save data to the player's character section
        # Length of the meta section + 4 bytes for the meta length number + 8 bytes for the total data length + 4 bytes for the character count
        player_offset += len(meta_b) + 4 + 8 + 4
        player_offset_b = qpack(player_offset)

        data_length = len(meta_b) + len(chara_byte) + 4 + 8 + 4
        data_length_b = qpack(data_length)

        unknown_b = ipack(self.unknown)

        data_chunks = [
            meta_i_b,
            meta_b,
            data_length_b,
            chara_l_b,
            chara_byte,
            unknown_b,
            player_offset_b,
        ]

        return b"".join(data_chunks)

    # Create the bytes for the character data section
    def _bytes_charas(self):
        ipack = struct.Struct("<I")

        player_offset = 0
        after_player = False

        chara_bytes = []
        for chara, chara_detail in zip(self.charas, self.chara_details):
            chara_detail_b, chara_detail_i = msg_pack(chara_detail)
            chara_detail_i_b = ipack.pack(chara_detail_i)
            chara_b = bytes(chara)

            # Convert the length of the character data to an integer
            chara_length = sum(map(lambda x: len(x), [chara_detail_i_b, chara_detail_b, chara_b]))
            chara_length_b = ipack.pack(chara_length)

            chara_byte = b"".join([chara_length_b, chara_detail_i_b, chara_detail_b, chara_b])

            if chara_detail["charasGameParam"]["isPC"]:
                after_player = True

            # If the player's character hasn't appeared yet, keep adding to the offset
            if not after_player:
                player_offset += len(chara_byte)

            chara_bytes.append(chara_byte)

        return b"".join(chara_bytes), player_offset

    def save(self, filename):
        with open(filename, "wb") as f:
            f.write(bytes(self))

    # Create an adjacency matrix representing the interaction data between characters
    def generate_memory_matrix(self, command=0, active=True, decision="yes"):
        interract = "activeCommand" if active else "passiveCommand"

        assert interract in ["activeCommand", "passiveCommand"]
        assert decision in ["yes", "no"]

        rows = {}
        for c in self.chara_details:
            from_index = c["charasGameParam"]["Index"]
            row = {}
            table = c["charasGameParam"]["memory"][interract]["DeadTable"]

            for d in self.chara_details:
                to_index = d["charasGameParam"]["Index"]

                if to_index in table and command in table[to_index]["save"]["infos"]:
                    value = table[to_index]["save"]["infos"][command]["countInfo"][decision]
                else:
                    value = None

                row[f"{to_index}:{self.names[to_index]}"] = value

            rows[f"{from_index}:{self.names[from_index]}"] = row

        return pd.DataFrame.from_dict(rows).T

    # Create an adjacency matrix representing the sexual interaction data between characters
    def generate_sexual_memory_matrix(self, command):
        rows = {}
        for c in self.chara_details:
            from_index = c["charasGameParam"]["Index"]
            row = {}
            table = c["charasGameParam"]["memory"]["pairTable"]

            for d in self.chara_details:
                to_index = d["charasGameParam"]["Index"]
                if from_index == to_index:
                    continue
                value = table[to_index]["saveInfo"][command]
                row[f"{to_index}:{self.names[to_index]}"] = value

            rows[f"{from_index}:{self.names[from_index]}"] = row

        return pd.DataFrame.from_dict(rows).T
