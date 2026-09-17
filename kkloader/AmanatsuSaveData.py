"""Amanatsu Location save data loader and serializer.

An Amanatsu Location save is a small custom container around MemoryPack's
version-tolerant objects::

    [i32 coreLen][SaveData core]
    [i32 playerLen][PlayerData]
    [i32 npcSlotCount]
      npcSlotCount x ([i32 npcLen][NPCData or FF for null])

The public shape intentionally follows ``kkloader.AicomiSaveData`` so this
module can later be moved into KoikatuCharaLoader with minimal adjustment:

* ``core`` is an editable dict for the leading ``AL.User.SaveData`` object.
* ``player`` and each non-null item in ``npcs`` have ``type``, ``chara`` and
  editable ``fields`` entries.
* ``records`` and ``charas`` expose convenient flattened views.
* ``bytes(save)`` and ``save(path)`` serialize all edits.

Unknown/reserved version-tolerant members are kept as raw bytes.  Loading is
strict: every object and every embedded ``AmanatsuCharaData`` is immediately
re-encoded and required to match the original bytes.  A schema error therefore
fails during load instead of producing a subtly corrupted save later.
"""

from __future__ import annotations

import io
import struct
from pathlib import Path
from typing import Any, BinaryIO, Optional, Union

from kkloader import AmanatsuCharaData
from kkloader.funcs import to_stream
from kkloader.MemoryPack import (
    MpReader,
    MpWriter,
    read_byte_array,
    read_primitive_array,
    read_version_string,
    write_byte_array,
    write_primitive_array,
    write_version_string,
)

FileLike = Union[str, Path, bytes, io.BytesIO]
Schema = list[tuple[str, Any]]


# ---------------------------------------------------------------------------
# Primitive and version-tolerant MemoryPack codec
# ---------------------------------------------------------------------------


def _read_int_float_dictionary(reader: MpReader) -> dict[int, float] | None:
    count = reader.collection_header()
    if count is None:
        return None
    if not 0 <= count <= 1_000_000:
        raise ValueError(f"implausible dictionary count {count}")
    return {reader.i32(): reader.f32() for _ in range(count)}


def _write_int_float_dictionary(writer: MpWriter, value: dict[int, float] | None) -> None:
    if value is None:
        writer.collection_header(None)
        return
    writer.collection_header(len(value))
    for key, item in value.items():
        writer.i32(key)
        writer.f32(item)


def _read_spec(reader: MpReader, spec: Any) -> Any:
    if spec == "i32":
        return reader.i32()
    if spec == "u64":
        return reader.u64()
    if spec == "bool":
        return reader.boolean()
    if spec == "str":
        return reader.string()
    if spec == "version":
        return read_version_string(reader, max_components=16)
    if spec == "bytes":
        return read_byte_array(reader)
    if spec == "ints":
        return read_primitive_array(reader, "int", max_count=1_000_000)
    if spec == "ikd_float":
        return _read_int_float_dictionary(reader)
    if isinstance(spec, tuple) and len(spec) == 2 and spec[0] == "object":
        return _read_versioned_object(reader, spec[1])
    raise ValueError(f"unknown reader spec {spec!r}")


def _write_spec(writer: MpWriter, spec: Any, value: Any) -> None:
    if spec == "i32":
        writer.i32(value)
    elif spec == "u64":
        writer.u64(value)
    elif spec == "bool":
        writer.boolean(value)
    elif spec == "str":
        writer.string(value)
    elif spec == "version":
        write_version_string(writer, value)
    elif spec == "bytes":
        write_byte_array(writer, value)
    elif spec == "ints":
        write_primitive_array(writer, "int", value)
    elif spec == "ikd_float":
        _write_int_float_dictionary(writer, value)
    elif isinstance(spec, tuple) and len(spec) == 2 and spec[0] == "object":
        writer.raw(_encode_versioned_object(value, spec[1]))
    else:
        raise ValueError(f"unknown writer spec {spec!r}")


def _member(schema: Schema, index: int) -> tuple[str, Any]:
    if index < len(schema):
        return schema[index]
    return f"_unknown_{index}", None


def _read_versioned_object(reader: MpReader, schema: Schema) -> dict[str, Any] | None:
    """Read one MemoryPack version-tolerant object.

    Each member is decoded inside its recorded byte boundary.  ``None`` specs
    and members newer than this schema stay as raw bytes.
    """

    count = reader.object_header()
    if count is None:
        return None
    lengths = [reader.varint() for _ in range(count)]
    if any(length < 0 for length in lengths):
        raise ValueError(f"negative member length in {lengths!r}")

    result: dict[str, Any] = {"_member_count": count}
    for index, length in enumerate(lengths):
        payload = reader._take(length)
        name, spec = _member(schema, index)
        if spec is None:
            result[name] = payload
            continue
        child = MpReader(payload)
        result[name] = _read_spec(child, spec)
        if child.pos != len(payload):
            raise ValueError(f"member {name} consumed {child.pos}/{len(payload)} bytes")
    return result


def _decode_versioned_object(blob: bytes, schema: Schema) -> dict[str, Any] | None:
    reader = MpReader(blob)
    value = _read_versioned_object(reader, schema)
    if reader.pos != len(blob):
        raise ValueError(f"version-tolerant object consumed {reader.pos}/{len(blob)} bytes")
    return value


def _encode_versioned_object(value: dict[str, Any] | None, schema: Schema) -> bytes:
    if value is None:
        return b"\xff"
    count = value["_member_count"]
    if not 0 <= count <= 254:
        raise ValueError(f"invalid member count {count}")

    payloads: list[bytes] = []
    for index in range(count):
        name, spec = _member(schema, index)
        item = value[name]
        if spec is None:
            if not isinstance(item, (bytes, bytearray)):
                raise ValueError(f"raw member {name} must contain bytes")
            payloads.append(bytes(item))
        else:
            child = MpWriter()
            _write_spec(child, spec, item)
            payloads.append(child.bytes())

    writer = MpWriter()
    writer.object_header(count)
    for payload in payloads:
        writer.varint(len(payload))
    for payload in payloads:
        writer.raw(payload)
    return writer.bytes()


# ---------------------------------------------------------------------------
# AL.User wire schemas recovered from full-game IL2CPP metadata
# ---------------------------------------------------------------------------


PARAMETER_INFO_SCHEMA: Schema = [
    ("Point", "i32"),
    ("LV", "i32"),
    ("IsMaxLv", "bool"),
]

GAME_PARAMETER_SCHEMA: Schema = [
    ("Favorability", ("object", PARAMETER_INFO_SCHEMA)),
    ("LatePoint", "i32"),
    ("Inclusiveness", ("object", PARAMETER_INFO_SCHEMA)),
    ("Proactivity", ("object", PARAMETER_INFO_SCHEMA)),
    ("Curiosity", ("object", PARAMETER_INFO_SCHEMA)),
    ("Cost", "i32"),
]

ACTION_STATE_SCHEMA: Schema = [
    ("_version", "version"),
    ("LinkPartnerUniqueID", "i32"),
    ("MapID", "i32"),
]

GAME_COUNT_SCHEMA: Schema = [
    ("_version", "version"),
    ("TimeZonePlayCommand", "i32"),
    ("IsTimeZoneH", "bool"),
    ("ActionMotionID", "i32"),
    ("IsNightH", "bool"),
    ("IsH", "bool"),
    ("NightEventCount", "i32"),
    ("NextMotionID", "i32"),
    ("H", "i32"),
    ("Massage", "i32"),
]

H_PARAMETER_SCHEMA: Schema = [("GaugeStage", "ints")]

CYCLE_SCHEMA: Schema = [
    ("_reserved_0", None),
    ("TimeZone", "i32"),
]

CORE_SCHEMA: Schema = [
    ("LoadProductID", "i32"),
    ("Version", "version"),
    ("SaveTimeText", "str"),
    ("Cycle", ("object", CYCLE_SCHEMA)),
    ("TutorialProgress", "i32"),
    ("EntryCount", "i32"),
    ("Comment", "str"),
    ("IsItemEvent", "bool"),
]

# ActorData has no serialized order-0 member and reserves orders 12..19.  The
# zero-length entries still exist in MemoryPack's version-tolerant length table.
PLAYER_SCHEMA: Schema = [
    ("_reserved_0", None),
    ("CharaFileName", "str"),
    ("UniqueID", "i32"),
    ("_humanFileBinary", "bytes"),
    ("_version", "version"),
    ("IsFutanari", "bool"),
    ("_reserved_6", None),
    ("_reserved_7", None),
    ("_reserved_8", None),
    ("_reserved_9", None),
    ("_reserved_10", None),
    ("_reserved_11", None),
    ("_reserved_12", None),
    ("_reserved_13", None),
    ("_reserved_14", None),
    ("_reserved_15", None),
    ("_reserved_16", None),
    ("_reserved_17", None),
    ("_reserved_18", None),
    ("_reserved_19", None),
    ("DataID", "str"),
    ("UserID", "str"),
]

NPC_SCHEMA: Schema = [
    ("_reserved_0", None),
    ("CharaFileName", "str"),
    ("UniqueID", "i32"),
    ("_humanFileBinary", "bytes"),
    ("_version", "version"),
    ("Action", ("object", ACTION_STATE_SCHEMA)),
    ("_animationSpeedAmplitude", "ikd_float"),
    ("GameParameter", ("object", GAME_PARAMETER_SCHEMA)),
    ("GameCount", ("object", GAME_COUNT_SCHEMA)),
    ("SaveTimeText", "str"),
    ("EntryTime", "u64"),
    ("HParameter", ("object", H_PARAMETER_SCHEMA)),
    ("_reserved_12", None),
    ("_reserved_13", None),
    ("_reserved_14", None),
    ("_reserved_15", None),
    ("_reserved_16", None),
    ("_reserved_17", None),
    ("_reserved_18", None),
    ("_reserved_19", None),
    ("DataID", "str"),
    ("UserID", "str"),
]

RECORD_SCHEMAS: dict[str, Schema] = {
    "PlayerData": PLAYER_SCHEMA,
    "NPCData": NPC_SCHEMA,
}


# Public codec helpers mirror those exposed by AicomiSaveData.py.
def decode_core(blob: bytes) -> dict[str, Any] | None:
    return _decode_versioned_object(blob, CORE_SCHEMA)


def encode_core(fields: dict[str, Any] | None) -> bytes:
    return _encode_versioned_object(fields, CORE_SCHEMA)


def decode_record(blob: bytes, schema: Schema) -> dict[str, Any] | None:
    return _decode_versioned_object(blob, schema)


def encode_record(fields: dict[str, Any], card: bytes | None, schema: Schema) -> bytes:
    serializable = dict(fields)
    serializable["_humanFileBinary"] = card
    return _encode_versioned_object(serializable, schema)


# ---------------------------------------------------------------------------
# Save container class
# ---------------------------------------------------------------------------


def _read_exact(stream: BinaryIO, count: int, label: str) -> bytes:
    data = stream.read(count)
    if len(data) != count:
        raise EOFError(f"{label}: expected {count} bytes, got {len(data)}")
    return data


def _read_i32(stream: BinaryIO, label: str) -> int:
    return struct.unpack("<i", _read_exact(stream, 4, label))[0]


def _read_record(stream: BinaryIO, label: str) -> bytes:
    length = _read_i32(stream, f"{label}.length")
    if length < 0:
        raise ValueError(f"{label}: negative length {length}")
    return _read_exact(stream, length, label)


class AmanatsuSaveData:
    """Load, edit and serialize an Amanatsu Location save file."""

    def __init__(self) -> None:
        self.core: dict[str, Any] = {}
        self.player: dict[str, Any] = {}
        self.npcs: list[Optional[dict[str, Any]]] = []
        self.names: dict[int, str] = {}
        self.original_file_path: Optional[str] = None

    @classmethod
    def load(cls, filelike: FileLike) -> "AmanatsuSaveData":
        """Load a save and prove that every decoded component round-trips."""

        save = cls()
        stream, save.original_file_path = to_stream(filelike)

        save.core = cls._load_core(_read_record(stream, "SaveData"))
        save.player = cls._load_actor(_read_record(stream, "PlayerData"), "PlayerData")

        npc_count = _read_i32(stream, "NPCDataList.count")
        if not 0 <= npc_count <= 30:
            raise ValueError(f"implausible NPC slot count {npc_count}")
        save.npcs = []
        for index in range(npc_count):
            blob = _read_record(stream, f"NPCData[{index}]")
            save.npcs.append(None if blob == b"\xff" else cls._load_actor(blob, "NPCData"))

        if stream.read(1):
            raise ValueError("trailing data after the last NPC record")

        save._refresh_names()
        return save

    @staticmethod
    def _load_core(blob: bytes) -> dict[str, Any]:
        fields = decode_core(blob)
        if fields is None or encode_core(fields) != blob:
            raise ValueError("SaveData core does not re-encode byte-exactly")
        return fields

    @staticmethod
    def _load_actor(blob: bytes, type_name: str) -> dict[str, Any]:
        schema = RECORD_SCHEMAS[type_name]
        fields = decode_record(blob, schema)
        if fields is None:
            raise ValueError(f"cannot decode {type_name}")
        card = fields.pop("_humanFileBinary", None)
        if card is None:
            raise ValueError(f"{type_name} has no embedded character card")
        if encode_record(fields, card, schema) != blob:
            raise ValueError(f"{type_name} does not re-encode byte-exactly")

        chara = AmanatsuCharaData.load(card)
        if bytes(chara) != card:
            raise ValueError(f"embedded character card in {type_name} does not round-trip byte-exactly")
        return {"type": type_name, "chara": chara, "fields": fields}

    @property
    def records(self) -> list[dict[str, Any]]:
        """Player followed by all occupied NPC slots, in file order."""

        return [self.player] + [npc for npc in self.npcs if npc is not None]

    @property
    def charas(self) -> list[AmanatsuCharaData]:
        """Character cards for ``records``, in the same order."""

        return [record["chara"] for record in self.records]

    def _refresh_names(self) -> None:
        self.names = {}
        for index, record in enumerate(self.records):
            parameter = record["chara"]["Parameter"].data
            last = str(parameter.get("lastname", "")).strip()
            first = str(parameter.get("firstname", "")).strip()
            self.names[index] = f"{last} {first}".strip()

    def __bytes__(self) -> bytes:
        """Serialize core, editable actor fields and character-card edits."""

        pack_i32 = struct.Struct("<i").pack

        def length_prefixed(blob: bytes) -> bytes:
            return pack_i32(len(blob)) + blob

        def actor_bytes(record: dict[str, Any]) -> bytes:
            type_name = record["type"]
            return encode_record(
                record["fields"],
                bytes(record["chara"]),
                RECORD_SCHEMAS[type_name],
            )

        chunks = [
            length_prefixed(encode_core(self.core)),
            length_prefixed(actor_bytes(self.player)),
            pack_i32(len(self.npcs)),
        ]
        for npc in self.npcs:
            blob = b"\xff" if npc is None else actor_bytes(npc)
            chunks.append(length_prefixed(blob))
        return b"".join(chunks)

    def save(self, filename: str | Path) -> None:
        """Write the current object state to ``filename``."""

        with open(filename, "wb") as stream:
            stream.write(bytes(self))

    def __repr__(self) -> str:
        return f"AmanatsuSaveData(charas={len(self.charas)}, save_time={self.core.get('SaveTimeText')!r})"


__all__ = [
    "AmanatsuSaveData",
    "CORE_SCHEMA",
    "PLAYER_SCHEMA",
    "NPC_SCHEMA",
    "RECORD_SCHEMAS",
    "decode_core",
    "encode_core",
    "decode_record",
    "encode_record",
]
