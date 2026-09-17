"""Aicomi save data loader and serializer.

An Aicomi save file is a sequence of length-prefixed sections written by
`AC.User.SaveData.Save()` (MemoryPack-based, but with custom framing):

    [i32 coreLen][SaveData core MemoryPack object]
    [i32 len][PlayerData record]                      # exactly one
    [i32 tag]                                         # constant 3, meaning TBD
    [i32 nNPC]                                        # NPCDataList capacity
      nNPC x ( [i32 len][NPCData record] )            # empty slot = [i32 1][0xFF]
    [i32 0][i32 0]                                    # constants, meaning TBD
    [i32 nUnique]
      nUnique x ( [i32 index][i32 len][UniqueNPCData record] )
    EOF (exact)

Each actor record embeds a standard Aicomi character card (`_humanFileBinary`)
that `AicomiCharaData` decodes. The record's other members (FavorValue etc.)
are decoded into an editable "fields" dict via the wire schemas in the second
half of this module and re-encoded from it on serialization, so both the
card and the fields can be modified. Decoding is strict: everything must
decode fully and re-encode byte-exactly at load time (a mismatch raises), so
an unmodified save always round-trips byte-exactly and a schema bug surfaces
immediately instead of corrupting a save. The only members carried as raw
`bytes` are those behind hand-written formatters whose wire format is not
reverse-engineered (`Cycle` etc. in the core).
"""

from __future__ import annotations

import io
import struct
from typing import Any, Dict, List, Optional, Tuple, Union

from kkloader import AicomiCharaData
from kkloader.funcs import load_length, load_type, to_stream
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


class AicomiSaveData:
    """Load and serialize Aicomi save data.

    Attributes:
        core: editable member dict of the leading SaveData core object
            (SaveTimeText, Comment, MapID, ...; members behind custom
            formatters are raw `bytes`).
        player: the player's record (see `_load_record` for the dict layout).
        npcs: NPC slots in file order; None marks an empty slot.
        uniques: unique-NPC records, each carrying its "index".
        tag / zeros: constants preserved verbatim from the file.
        names: {index: "lastname firstname"} over `charas`.
    """

    def __init__(self) -> None:
        """Initialize an empty save data container."""
        self.core: Dict[str, Any] = {}
        self.player: Dict[str, Any] = {}
        self.tag: int = 0
        self.npcs: List[Optional[Dict[str, Any]]] = []
        self.zeros: Tuple[int, int] = (0, 0)
        self.uniques: List[Dict[str, Any]] = []
        self.names: Dict[int, str] = {}
        self.original_file_path: Optional[str] = None

    @classmethod
    def load(cls, filelike: Union[str, bytes, io.BytesIO]) -> "AicomiSaveData":
        """Load an Aicomi save file into a new instance."""
        acs = cls()
        data_stream, acs.original_file_path = to_stream(filelike)

        # SaveData core MemoryPack object (version-tolerant layout; fully
        # decoded, unknown members kept as raw bytes)
        acs.core = cls._load_core(load_length(data_stream, "<i"))
        # The player's actor record
        acs.player = cls._load_record(load_length(data_stream, "<i"), "PlayerData")
        # Was set to `3`, but the details are unclear
        acs.tag = load_type(data_stream, "<i")

        # NPCDataList: fixed capacity, empty slots are a single 0xFF (null object)
        npc_num = load_type(data_stream, "<i")
        acs.npcs = []
        for _ in range(npc_num):
            blob = load_length(data_stream, "<i")
            acs.npcs.append(None if blob == b"\xff" else cls._load_record(blob, "NPCData"))

        # Two constants observed as `0`, meaning unclear
        acs.zeros = (load_type(data_stream, "<i"), load_type(data_stream, "<i"))

        # UniqueNPCList: each record is preceded by its index
        unique_num = load_type(data_stream, "<i")
        acs.uniques = []
        for _ in range(unique_num):
            index = load_type(data_stream, "<i")
            record = cls._load_record(load_length(data_stream, "<i"), "UniqueNPCData")
            record["index"] = index
            acs.uniques.append(record)

        if data_stream.read(1):
            raise ValueError("trailing data after the last unique-NPC record")

        acs.names = {}
        for i, chara in enumerate(acs.charas):
            acs.names[i] = f"{chara['Parameter']['lastname']} {chara['Parameter']['firstname']}"

        return acs

    @classmethod
    def _load_record(cls, blob: bytes, type_name: str) -> Dict[str, Any]:
        """Decode one actor record blob into editable "fields" plus "chara".

        `type_name` is determined by which file section the record came from
        (player / NPC list / unique-NPC list) and selects the wire schema.
        The decode must re-encode byte-exactly, so a schema mismatch raises
        instead of risking a corrupted rewrite.
        """
        schema = RECORD_SCHEMAS[type_name]
        fields = decode_record(blob, schema)
        if fields is None or fields.get("_humanFileBinary") is None:
            raise ValueError(f"cannot parse {type_name} record")
        card = fields.pop("_humanFileBinary")
        if encode_record(fields, card, schema) != blob:
            raise ValueError(f"{type_name} record does not re-encode byte-exactly")
        chara = AicomiCharaData.load(card)
        if bytes(chara) != card:
            raise ValueError("embedded character card does not round-trip byte-exactly")
        return {"type": type_name, "chara": chara, "fields": fields}

    @staticmethod
    def _load_core(blob: bytes) -> Dict[str, Any]:
        """Decode the SaveData core object into an editable member dict.

        Like `_load_record`, the decode must re-encode byte-exactly or a
        ValueError is raised."""
        fields = decode_core(blob)
        if fields is None or encode_core(fields) != blob:
            raise ValueError("cannot parse the SaveData core object")
        return fields

    @property
    def records(self) -> List[Dict[str, Any]]:
        """All actor records in file order (player, NPCs, unique NPCs)."""
        return [self.player] + [n for n in self.npcs if n is not None] + self.uniques

    @property
    def charas(self) -> List[AicomiCharaData]:
        """The character card of every record, in file order."""
        return [r["chara"] for r in self.records]

    # Save Data Serialization
    def __bytes__(self) -> bytes:
        """Serialize the save data to bytes.

        Each record is re-encoded from its editable "fields" dict (with the
        re-serialized character card embedded), so both card edits and field
        edits (FavorValue etc.) are reflected. An unmodified save round-trips
        byte-exactly.
        """
        ipack = struct.Struct("<i").pack

        def record_bytes(record: Dict[str, Any]) -> bytes:
            return encode_record(record["fields"], bytes(record["chara"]), RECORD_SCHEMAS[record["type"]])

        core_b = encode_core(self.core)
        player_b = record_bytes(self.player)
        data_chunks = [
            ipack(len(core_b)),
            core_b,
            ipack(len(player_b)),
            player_b,
            ipack(self.tag),
            ipack(len(self.npcs)),
        ]
        for npc in self.npcs:
            if npc is None:
                data_chunks += [ipack(1), b"\xff"]
            else:
                npc_b = record_bytes(npc)
                data_chunks += [ipack(len(npc_b)), npc_b]
        data_chunks += [ipack(self.zeros[0]), ipack(self.zeros[1]), ipack(len(self.uniques))]
        for unique in self.uniques:
            unique_b = record_bytes(unique)
            data_chunks += [ipack(unique["index"]), ipack(len(unique_b)), unique_b]

        return b"".join(data_chunks)

    def save(self, filename: str) -> None:
        """Write the serialized save data to a file."""
        with open(filename, "wb") as f:
            f.write(bytes(self))

    def __repr__(self) -> str:
        return f"AicomiSaveData(charas={len(self.charas)}, save_time={self.core.get('SaveTimeText')!r})"


# ===========================================================================
# Wire schemas and codec for the actor records
# (PlayerData / NPCData / UniqueNPCData)
#
# Ground truth: Ghidra decompiles of the generated `*Formatter.Deserialize`
# methods plus the `[MemoryPackConstructor]` signatures in `il2cpp_dump/dump.cs`.
# Key facts this section encodes:
#
# * Slot order — MemoryPack lays members out by `[MemoryPackOrder]`, merging
#   base-class and own members; on an order tie the base member comes first,
#   and unordered members go last. So e.g. PlayerData's `_version` (own,
#   order 5) sits right after `CharaFileName` (base, order 5) — NOT after
#   `PartnerGuid`.
# * System.Version — `[u8 count | 0xFF=null][count x i32]` (count is 4).
# * Nullable<AssignGuid> — 12 bytes fixed: `[i32 group][i32 index][i32 has]`.
# * Unmanaged runs — consecutive unmanaged members are block-copied; the
#   per-member sizes below reproduce the exact block sizes seen in the
#   decompile (e.g. NPCData's Favor..VisitNumber 29-byte run).
# * Versioning — the leading member-count byte says how many slots follow,
#   so older builds (NPCData 44, UniqueNPCData 28) parse with the same tables.
#
# Every record decode is gated on landing exactly on the record boundary
# read by `AicomiSaveData.load`; a mismatch discards the decode
# (no wrong values ever surface — raw is better than wrong).
# ===========================================================================

# ---------------------------------------------------------------------------
# readers for the leaf wire types
# ---------------------------------------------------------------------------


def _assign_guid(r: MpReader) -> dict[str, int]:
    """AssignGuid — 8 bytes: int Group, int Index."""
    return {"group": r.i32(), "index": r.i32()}


def _nullable_assign_guid(r: MpReader) -> dict[str, int] | None:
    """Nullable<AssignGuid> — 12 bytes fixed (hand-written formatter)."""
    g, i, has = r.i32(), r.i32(), r.i32()
    return {"group": g, "index": i} if has else None


def _status(r: MpReader) -> str | None:
    """Status — 1-byte member count + 30-byte unmanaged block (31B fixed).

    Kept as the hex of all 31 bytes (member count included) so it can be
    written back verbatim by `encode_record`.
    """
    mc = r.u8()
    if mc == 0xFF:
        return None
    return (bytes([mc]) + r._take(30)).hex()


def _version(r: MpReader) -> str | None:
    """System.Version — [u8 count|0xFF][count x i32] (-1 = unset component)."""
    return read_version_string(r, max_components=8)


def _arr_f32(r: MpReader) -> list[float] | None:
    return read_primitive_array(r, "float", max_count=1_000_000)


def _list_guid8(r: MpReader) -> list[dict[str, int]] | None:
    """List<AssignGuid> — [i32 n][n x 8B]."""
    n = r.collection_header()
    if n is None:
        return None
    if not 0 <= n <= 100_000:
        raise ValueError(f"implausible collection count {n}")
    return [_assign_guid(r) for _ in range(n)]


def _nullable_i32(r: MpReader) -> int | None:
    """Nullable<int> unmanaged — [4B hasValue][4B value]."""
    has = r.i32()
    v = r.i32()
    return v if has else None


def _ikd(r: MpReader, read_value) -> dict[int, Any] | None:
    """IntKeyDictionary<V> — [i32 n][n x (i32 key, V value)]."""
    n = r.collection_header()
    if n is None:
        return None
    if not 0 <= n <= 1_000_000:
        raise ValueError(f"implausible dictionary count {n}")
    out: dict[int, Any] = {}
    for _ in range(n):
        k = r.i32()
        out[k] = read_value(r)
    return out


def _int_jagged(r: MpReader) -> list | None:
    """int[][] — [i32 n][n x int[]]."""
    n = r.collection_header()
    if n is None:
        return None
    if not 0 <= n <= 100_000:
        raise ValueError(f"implausible jagged count {n}")
    return [read_primitive_array(r, "int", max_count=1_000_000) for _ in range(n)]


# ---------------------------------------------------------------------------
# generic MemoryPack object reader (versioning-aware)
# ---------------------------------------------------------------------------

# member spec: (name, reader) where reader is str key of _LEAF or a callable
_LEAF: dict[str, Any] = {
    "i32": MpReader.i32,
    "u8": MpReader.u8,
    "u32": MpReader.u32,
    "bool": MpReader.boolean,
    "f32": MpReader.f32,
    "str": MpReader.string,
    "guid8": _assign_guid,
    "nguid12": _nullable_assign_guid,
    "status": _status,
    "version": _version,
    "nint": _nullable_i32,
    "bytes": lambda r: _to_list(read_byte_array(r, max_count=1_000_000)),
    "bools": lambda r: _to_bools(read_byte_array(r, max_count=1_000_000)),
    "ints": lambda r: read_primitive_array(r, "int", max_count=1_000_000),
    "floats": _arr_f32,
    "guids": _list_guid8,
    "raw2": lambda r: r._take(2).hex(),  # Nullable<sbyte>
    "raw8": lambda r: r._take(8).hex(),  # Nullable<enum>
    "raw16": lambda r: r._take(16).hex(),  # Nullable<Vector3>
}


def _to_list(b) -> list[int] | None:
    return None if b is None else list(b)


def _to_bools(b) -> list[bool] | None:
    return None if b is None else [x != 0 for x in b]


def _read_member(r: MpReader, spec: Any) -> Any:
    if callable(spec):
        return spec(r)
    return _LEAF[spec](r)


def _read_object(r: MpReader, members: list[tuple[str, Any]]) -> dict[str, Any] | None:
    """Read `[u8 memberCount][members...]`, honoring MemoryPack versioning:
    only the first `memberCount` members are present on the wire."""
    mc = r.u8()
    if mc == 0xFF:
        return None
    if mc > len(members):
        raise ValueError(f"object has {mc} members, schema knows {len(members)}")
    out: dict[str, Any] = {"_member_count": mc}
    for name, spec in members[:mc]:
        out[name] = _read_member(r, spec)
    return out


# ---------------------------------------------------------------------------
# nested game types
# ---------------------------------------------------------------------------

_DESIRE = [
    ("ID", "i32"),
    ("Current", "i32"),
    ("Prioritizes", "bool"),
    ("Order", "i32"),
    ("Tag", "str"),
]

_ACTION_DATA = [
    ("_id", "i32"),
    ("PointID", "nint"),
    ("ParameterID", "nint"),
    ("AnimationID", "nint"),
    ("TargetGuid", "nguid12"),
    ("Coordinate", "raw2"),
    ("MapID", "nint"),
    ("IsOnlyMapID", "bool"),
    ("Runs", "bool"),
    ("IsPriority", "bool"),
    ("Duration", "f32"),
    ("TimeToCancel", "f32"),
    ("Tag", "str"),
    ("BannedMaps", "ints"),
    ("EventID", "nint"),
    ("IsInterruptable", "bool"),
    ("Targets", "guids"),
    ("Observer", "nguid12"),
    ("SyncSub", "bool"),
    ("ActionIndex", "i32"),
]


def _action_data(r: MpReader):
    return _read_object(r, _ACTION_DATA)


def _stack_action_data(r: MpReader):
    n = r.i32()
    if n == -1:
        return None
    if not 0 <= n <= 10_000:
        raise ValueError(f"implausible stack count {n}")
    return [_action_data(r) for _ in range(n)]


_NPC_ACTION_STATE = [
    ("_version", "version"),
    ("_actionID", "i32"),
    ("RemainedTime", "f32"),
    ("Coordinate", "i8_"),  # sbyte
    ("TargetCharaKey", "nguid12"),
    ("Arrived", "bool"),
    ("IsPriority", "bool"),
    ("RequiresDressing", "bool"),
    ("IsLunch", "bool"),
    ("ActionHistory", "ints"),
    ("PriorityActionQueue", "ints"),
    ("PriorityActionHash", "ints"),
    ("ScheduledAction", _stack_action_data),
    ("MapQueue", "ints"),
    ("State", "i32"),
    ("PointID", "nint"),
    ("ParameterID", "nint"),
    ("AnimationID", "nint"),
    ("Duration", "f32"),
    ("EventID", "nint"),
    ("PrevState", "raw8"),
    ("Position", "raw16"),
    ("HubPoints", "ints"),
    ("BasedActions", _stack_action_data),
    ("IsInterruptable", "bool"),
    ("IsEndless", "bool"),
    ("Targets", "guids"),
    ("Observer", "nguid12"),
    ("RemainedTimeToCancel", "f32"),
    ("IsInProgressSex", "bool"),
    ("SyncSub", "bool"),
    ("StateCacheForShy", "raw8"),
    ("RecentTakeOffMapID", "i32"),
    ("ActionIndex", "i32"),
]
_LEAF["i8_"] = MpReader.i8


def _npc_action_state(r: MpReader):
    return _read_object(r, _NPC_ACTION_STATE)


_UNIQUE_ACTION_STATE = [
    ("ID", "i32"),
    ("PointID", "nint"),
    ("AnimationID", "nint"),
    ("Coordinate", "raw2"),
    ("EventID", "nint"),
]


def _unique_action_state(r: MpReader):
    return _read_object(r, _UNIQUE_ACTION_STATE)


_TALK_STATS = [
    ("_version", "version"),
    ("EventMemory", "ints"),
    ("_talkStrikeZone", "bytes"),
    ("Asked", "bool"),
    ("TopicListen", "ints"),
    ("MaxTime", "i32"),
    ("Time", "i32"),
    ("AcquiredPoint", "bool"),
    ("InvitedLunch", "bool"),
    ("IntroHistory", "ints"),
    ("_commandHistory", "ints"),
    ("IntroMemory", "ints"),
]


def _talk_stats(r: MpReader):
    return _read_object(r, _TALK_STATS)


def _desire_table(r: MpReader):
    return _read_object(r, [("_instance", lambda rr: _ikd(rr, lambda x: _read_object(x, _DESIRE)))])


def _ikd_float(r: MpReader):
    return _ikd(r, MpReader.f32)


def _ikd_int(r: MpReader):
    return _ikd(r, MpReader.i32)


def _talk_patterns(r: MpReader):
    """IntKeyDictionary<IntKeyDictionary<int[][]>>."""
    return _ikd(r, lambda rr: _ikd(rr, _int_jagged))


def _ikd_intset(r: MpReader):
    """IntKeyDictionary<HashSet<int>> — the set is a plain [i32 n][n x i32]."""
    return _ikd(r, lambda rr: read_primitive_array(rr, "int", max_count=1_000_000))


def _ikd_ikd_intset(r: MpReader):
    """IntKeyDictionary<IntKeyDictionary<HashSet<int>>>."""
    return _ikd(r, _ikd_intset)


# ---------------------------------------------------------------------------
# record schemas (wire order — base/own merged by [MemoryPackOrder])
# ---------------------------------------------------------------------------


def _card(r: MpReader) -> bytes | None:
    """`_humanFileBinary` — the embedded character card, returned raw;
    `AicomiSaveData._load_record` turns it into an `AicomiCharaData`."""
    n = r.i32()
    if n == -1:
        return None
    if n < 0:
        raise ValueError(f"bad card length {n}")
    return r._take(n)


_ACTOR_HEAD: list[tuple[str, Any]] = [
    ("CallsignID", "i32"),  # base o0
    ("DisplayCallsign", "str"),  # base o1
    ("Guid", "guid8"),  # base o2
    ("Status", "status"),  # base o3
    ("_humanFileBinary", _card),  # base o4 — the character card
    ("CharaFileName", "str"),  # base o5
]

PLAYER_DATA: list[tuple[str, Any]] = _ACTOR_HEAD + [
    ("_version", "version"),  # own o5
    ("_resistFlags", "ints"),  # base o6
    ("_tastes", "bytes"),  # own o6
    ("_unlockedParts", "bools"),  # base o7
    ("PartnerGuid", "nguid12"),  # base o8
    ("Plan", "u8"),  # own, unordered
]

NPC_DATA: list[tuple[str, Any]] = _ACTOR_HEAD + [
    ("_version", "version"),  # own o5
    ("_resistFlags", "ints"),  # base o6
    ("Action", _npc_action_state),  # own o6
    ("_unlockedParts", "bools"),  # base o7
    ("FavorValue", "i32"),  # own o7
    ("PartnerGuid", "nguid12"),  # base o8
    ("LewdnessValue", "i32"),  # own o8
    ("HCountValue", "i32"),  # own o9
    ("RelationValue", "u8"),  # own o10
    ("VisitNumber", "i32"),  # own o12
    ("_animationSpeedAmplitude", _ikd_float),  # o13
    ("DesireStats", _desire_table),  # o14
    ("TalkStats", _talk_stats),  # o15
    ("PeriodStartDay", "i32"),  # o16
    ("PeriodDay", "u8"),  # o17
    ("BehaviorType", "i32"),  # o18
    ("Mood", "i32"),  # o19
    ("PromisedFestival", "bool"),  # o21
    ("UrgentAction", _action_data),  # o22
    ("Intimacy", "i32"),  # o23
    ("_tasteFlags", "bools"),  # o24
    ("ArrangedDate", "bool"),  # o25
    ("ArrangedShoppingDate", "bool"),  # o26
    ("IsVirginFlag", "bool"),  # o27
    ("IsAnalVirginFlag", "bool"),  # o28
    ("IsRunning", "bool"),  # o29
    ("TouchCount", "i32"),  # o30
    ("Plan", "u8"),  # o31
    ("_sexperience", "i32"),  # o32
    ("DateCount", "i32"),  # o33
    ("_talkPatterns", _talk_patterns),  # o34
    ("_placeCountTable", _ikd_int),  # o35
    ("_fireworksCountTable", _ikd_int),  # o36
    ("FirstEventFlags", "ints"),  # o37
    ("InvokedPairEvent", "bool"),  # o38
    ("InvokedNorokeEvent", "bool"),  # o39
    ("_favorOutroFlags", "bools"),  # o40
    ("AppliedShyParameter", "bool"),  # o41
    ("ArrangedTripDate", "bool"),  # 46-member builds only
    ("TripCount", "i32"),  # 46-member builds only
]

UNIQUE_NPC_DATA: list[tuple[str, Any]] = _ACTOR_HEAD + [
    ("_version", "version"),  # own o5
    ("_resistFlags", "ints"),  # base o6
    ("ID", "i32"),  # own o6
    ("_unlockedParts", "bools"),  # base o7
    ("EventMemory", "ints"),  # own o7
    ("PartnerGuid", "nguid12"),  # base o8
    ("Action", _unique_action_state),  # own o8
    ("EventTriggerFlag", "bool"),  # o9
    ("FavorValue", "i32"),  # o10
    ("RelationValue", "u8"),  # o11
    ("HCountValue", "i32"),  # o12
    ("MaxTime", "i32"),  # o13
    ("Time", "i32"),  # o14
    ("LewdnessValue", "i32"),  # o15
    ("IsVirginFlag", "bool"),  # o16
    ("IsAnalVirginFlag", "bool"),  # o17
    ("_sexperience", "i32"),  # o18
    ("TalkCount", "i32"),  # o19
    ("FirstEventFlags", "ints"),  # o20
    ("_favorOutroFlags", "bools"),  # o21
    ("SteadyEvents", "ints"),  # o22
    ("EventFlag", "bool"),  # o23
    ("EventHistory", "ints"),  # o24 (29-member builds only)
]

# record type (known from the file section a record sits in) -> wire schema.
# The record's own member-count byte handles build differences: older builds
# just wrote fewer members, and only the first memberCount slots are on the
# wire (see `_read_object` / `_write_object`).
RECORD_SCHEMAS: dict[str, list[tuple[str, Any]]] = {
    "PlayerData": PLAYER_DATA,
    "NPCData": NPC_DATA,
    "UniqueNPCData": UNIQUE_NPC_DATA,
}

# AC.User.SaveData — unlike the actor records this object is serialized
# version-tolerant: [u8 memberCount][memberCount x varint length][payloads].
# The per-member length table lets unknown members be preserved as raw bytes,
# so a `None` spec marks members behind hand-written formatters whose wire
# format is unknown; their value in "fields" is the raw payload (`bytes`).
CORE_SCHEMA: list[tuple[str, Any]] = [
    ("LoadProductID", "i32"),  # o0
    ("Version", "version"),  # o1
    ("SaveTimeText", "str"),  # o2
    ("MapID", "i32"),  # o3
    ("ClubContents", _ikd_intset),  # o4
    ("ChangedRegLimit", "bool"),  # o5
    ("Comment", "str"),  # o6
    ("Cycle", None),  # o7 — custom formatter
    ("SaveType", "i32"),  # o8
    ("TutorialProgress", "i32"),  # o9
    ("MinimapMode", "i32"),  # o10
    ("EntryCount", "i32"),  # o11
    ("HeroineEventCount", "i32"),  # o12
    ("AreaEventCounter", "i32"),  # o13
    ("EventMemory", None),  # o14 — IntKeyDictionary<Counter>, Counter unknown
    ("AreaEventTable", _ikd_ikd_intset),  # o15
    ("CalledHistory", "guids"),  # o16
    ("FestivalCount", "u32"),  # o17
    ("IsFirstShopping", "bool"),  # o18
    ("DateEventHistories", "ints"),  # o19 HashSet<int>
    ("TalkedMaps", "ints"),  # o20 HashSet<int>
    ("ClickedRegistration", "bool"),  # o21
    ("ClickedReturnFromRegistration", "bool"),  # o22
    ("EnteredSeat", "bool"),  # o23
    ("EnteredSeatForRandom", "bool"),  # o24
    ("SkipsPrologue", "raw2"),  # o25 Nullable<bool>
    ("AreaID", "i32"),  # o26
    ("UnlockRuinsToH", "bool"),  # o27
]


def decode_record(blob: bytes, schema: list[tuple[str, Any]]) -> dict[str, Any] | None:
    """Fully decode one actor record blob against `schema` in a single pass.

    The record's leading member-count byte says how many schema members are on
    the wire (older game versions wrote fewer). Returns the decoded member
    dict only when the walk lands **exactly** on the end of the blob; returns
    None otherwise (never partial/misaligned values).
    """
    try:
        r = MpReader(blob)
        fields = _read_object(r, schema)
        if fields is None or r.pos != len(blob):
            return None
        return fields
    except Exception:  # noqa: BLE001 — any wire surprise means "don't decode"
        return None


def _core_member(i: int) -> tuple[str, Any]:
    """Schema entry for core member `i`; members past the schema (newer
    builds) get a generated name and are treated as raw."""
    return CORE_SCHEMA[i] if i < len(CORE_SCHEMA) else (f"_unknown_{i}", None)


def decode_core(blob: bytes) -> dict[str, Any] | None:
    """Decode the version-tolerant SaveData core object.

    The wire layout is [u8 memberCount][memberCount x varint length]
    [payloads]. Members with a known wire format must consume exactly their
    recorded length; members without one (spec None, e.g. `Cycle`) keep
    their raw payload `bytes` as the value, which the length table makes
    possible. Returns None when the walk cannot land exactly on the blob end.
    """
    try:
        r = MpReader(blob)
        mc = r.u8()
        if mc == 0xFF:
            return None
        lengths = [r.varint() for _ in range(mc)]
        fields: dict[str, Any] = {"_member_count": mc}
        for i, length in enumerate(lengths):
            if length < 0 or r.pos + length > len(blob):
                return None
            name, spec = _core_member(i)
            if spec is None:
                fields[name] = r._take(length)
                continue
            start = r.pos
            fields[name] = _read_member(r, spec)
            if r.pos - start != length:
                return None
        if r.pos != len(blob):
            return None
        return fields
    except Exception:  # noqa: BLE001 — any wire surprise means "don't decode"
        return None


# ---------------------------------------------------------------------------
# writers — mirror of every reader above, so decoded records can be edited
# and re-encoded. `encode_record(decode_record(blob), card) == blob` is
# verified at load time by `AicomiSaveData`; a mismatch downgrades the record
# to raw (read-only) so a wrong writer can never corrupt a save.
# ---------------------------------------------------------------------------


def _w_assign_guid(w: MpWriter, v: dict[str, int]) -> None:
    w.i32(v["group"])
    w.i32(v["index"])


def _w_nullable_assign_guid(w: MpWriter, v: dict[str, int] | None) -> None:
    if v is None:
        w.i32(0)
        w.i32(0)
        w.i32(0)
    else:
        w.i32(v["group"])
        w.i32(v["index"])
        w.i32(1)


def _w_status(w: MpWriter, v: str | None) -> None:
    if v is None:
        w.u8(0xFF)
        return
    b = bytes.fromhex(v)
    if len(b) != 31:
        raise ValueError(f"Status must be 31 bytes, got {len(b)}")
    w.raw(b)


def _w_nint(w: MpWriter, v: int | None) -> None:
    if v is None:
        w.i32(0)
        w.i32(0)
    else:
        w.i32(1)
        w.i32(v)


def _w_bytes(w: MpWriter, v: list[int] | None) -> None:
    write_byte_array(w, None if v is None else bytes(v))


def _w_bools(w: MpWriter, v: list[bool] | None) -> None:
    write_byte_array(w, None if v is None else bytes(1 if x else 0 for x in v))


def _w_ints(w: MpWriter, v: list[int] | None) -> None:
    write_primitive_array(w, "int", v)


def _w_floats(w: MpWriter, v: list[float] | None) -> None:
    write_primitive_array(w, "float", v)


def _w_guids(w: MpWriter, v: list[dict[str, int]] | None) -> None:
    if v is None:
        w.collection_header(None)
        return
    w.collection_header(len(v))
    for g in v:
        _w_assign_guid(w, g)


def _w_hex(w: MpWriter, v: str) -> None:
    w.raw(bytes.fromhex(v))


_LEAF_W: dict[str, Any] = {
    "i32": lambda w, v: w.i32(v),
    "u8": lambda w, v: w.u8(v),
    "u32": lambda w, v: w.u32(v),
    "bool": lambda w, v: w.boolean(v),
    "f32": lambda w, v: w.f32(v),
    "str": lambda w, v: w.string(v),
    "guid8": _w_assign_guid,
    "nguid12": _w_nullable_assign_guid,
    "status": _w_status,
    "version": write_version_string,
    "nint": _w_nint,
    "bytes": _w_bytes,
    "bools": _w_bools,
    "ints": _w_ints,
    "floats": _w_floats,
    "guids": _w_guids,
    "raw2": _w_hex,
    "raw8": _w_hex,
    "raw16": _w_hex,
    "i8_": lambda w, v: w.i8(v),
}


def _write_member(w: MpWriter, spec: Any, value: Any) -> None:
    if callable(spec):
        _CALLABLE_W[spec](w, value)
    else:
        _LEAF_W[spec](w, value)


def _write_object(w: MpWriter, obj: dict[str, Any] | None, members: list[tuple[str, Any]]) -> None:
    """Mirror of `_read_object`: writes the stored `_member_count` and exactly
    that many members, so versioned records keep their original layout."""
    if obj is None:
        w.u8(0xFF)
        return
    mc = obj["_member_count"]
    if mc > len(members):
        raise ValueError(f"object has {mc} members, schema knows {len(members)}")
    w.u8(mc)
    for name, spec in members[:mc]:
        _write_member(w, spec, obj[name])


def _w_action_data(w: MpWriter, v: dict[str, Any] | None) -> None:
    _write_object(w, v, _ACTION_DATA)


def _w_stack_action_data(w: MpWriter, v: list | None) -> None:
    if v is None:
        w.i32(-1)
        return
    w.i32(len(v))
    for x in v:
        _w_action_data(w, x)


def _w_npc_action_state(w: MpWriter, v: dict[str, Any] | None) -> None:
    _write_object(w, v, _NPC_ACTION_STATE)


def _w_unique_action_state(w: MpWriter, v: dict[str, Any] | None) -> None:
    _write_object(w, v, _UNIQUE_ACTION_STATE)


def _w_talk_stats(w: MpWriter, v: dict[str, Any] | None) -> None:
    _write_object(w, v, _TALK_STATS)


def _w_ikd(w: MpWriter, v: dict[int, Any] | None, write_value: Any) -> None:
    if v is None:
        w.i32(-1)
        return
    w.i32(len(v))
    for k, val in v.items():
        w.i32(k)
        write_value(w, val)


def _w_desire(w: MpWriter, v: dict[str, Any] | None) -> None:
    _write_object(w, v, _DESIRE)


def _w_desire_table(w: MpWriter, v: dict[str, Any] | None) -> None:
    if v is None:
        w.u8(0xFF)
        return
    mc = v["_member_count"]
    w.u8(mc)
    if mc >= 1:
        _w_ikd(w, v["_instance"], _w_desire)


def _w_ikd_float(w: MpWriter, v: dict[int, float] | None) -> None:
    _w_ikd(w, v, lambda ww, vv: ww.f32(vv))


def _w_ikd_int(w: MpWriter, v: dict[int, int] | None) -> None:
    _w_ikd(w, v, lambda ww, vv: ww.i32(vv))


def _w_int_jagged(w: MpWriter, v: list | None) -> None:
    if v is None:
        w.i32(-1)
        return
    w.i32(len(v))
    for x in v:
        _w_ints(w, x)


def _w_talk_patterns(w: MpWriter, v: dict | None) -> None:
    _w_ikd(w, v, lambda ww, vv: _w_ikd(ww, vv, _w_int_jagged))


def _w_ikd_intset(w: MpWriter, v: dict[int, Any] | None) -> None:
    _w_ikd(w, v, _w_ints)


def _w_ikd_ikd_intset(w: MpWriter, v: dict[int, Any] | None) -> None:
    _w_ikd(w, v, _w_ikd_intset)


# reader callable (as used in the schema tables) -> its writer counterpart.
# `_write_object`'s member specs that are lambdas never reach `_write_member`;
# their writers handle the nesting explicitly (e.g. `_w_desire_table`).
_CALLABLE_W: dict[Any, Any] = {
    _action_data: _w_action_data,
    _stack_action_data: _w_stack_action_data,
    _npc_action_state: _w_npc_action_state,
    _unique_action_state: _w_unique_action_state,
    _talk_stats: _w_talk_stats,
    _desire_table: _w_desire_table,
    _ikd_float: _w_ikd_float,
    _ikd_int: _w_ikd_int,
    _talk_patterns: _w_talk_patterns,
    _ikd_intset: _w_ikd_intset,
    _ikd_ikd_intset: _w_ikd_ikd_intset,
}


def encode_record(fields: dict[str, Any], card: bytes | None, schema: list[tuple[str, Any]]) -> bytes:
    """Re-encode a record decoded by `decode_record` back to wire bytes.

    `card` is the serialized character card to embed in the `_humanFileBinary`
    slot (its length prefix is recomputed).
    """
    mc = fields["_member_count"]
    if mc > len(schema):
        raise ValueError(f"record has {mc} members, schema knows {len(schema)}")
    w = MpWriter()
    w.u8(mc)
    for name, spec in schema[:mc]:
        if spec is _card:
            if card is None:
                w.i32(-1)
            else:
                w.i32(len(card))
                w.raw(card)
        else:
            _write_member(w, spec, fields[name])
    return w.bytes()


def encode_core(fields: dict[str, Any]) -> bytes:
    """Re-encode the SaveData core decoded by `decode_core`.

    The per-member length table is recomputed, so edited members of any size
    stay consistent. Members held as raw `bytes` are written back verbatim.
    """
    mc = fields["_member_count"]
    payloads: list[bytes] = []
    for i in range(mc):
        name, spec = _core_member(i)
        value = fields[name]
        if isinstance(value, (bytes, bytearray)):
            payloads.append(bytes(value))
        elif spec is None:
            raise ValueError(f"core member {name} has an unknown wire format; assign bytes")
        else:
            w = MpWriter()
            _write_member(w, spec, value)
            payloads.append(w.bytes())
    w = MpWriter()
    w.u8(mc)
    for p in payloads:
        w.varint(len(p))
    for p in payloads:
        w.raw(p)
    return w.bytes()
