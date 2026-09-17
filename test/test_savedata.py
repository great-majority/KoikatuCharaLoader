from kkloader import AicomiSaveData, AmanatsuSaveData, KoikatuSaveData, SummerVacationSaveData
from kkloader.MemoryPack import (
    MpReader,
    MpWriter,
    read_byte_array,
    read_primitive_array,
    read_version,
    read_version_string,
    write_byte_array,
    write_primitive_array,
    write_version,
    write_version_string,
)

import pytest


def test_savedata_vanilla(savedata_dir, tmp_path):
    with open(savedata_dir / "kk_savedata.dat", "rb") as f:
        raw_data = f.read()
    ks = KoikatuSaveData.load(savedata_dir / "kk_savedata.dat")
    out_path = tmp_path / "kk_savedata.dat"
    ks.save(str(out_path))
    ks2 = KoikatuSaveData.load(str(out_path))
    assert raw_data == bytes(ks)
    assert bytes(ks) == bytes(ks2)


def test_summervacation_savedata(savedata_dir, tmp_path):
    with open(savedata_dir / "sv_savedata.dat", "rb") as f:
        raw_data = f.read()
    svsd = SummerVacationSaveData.load(savedata_dir / "sv_savedata.dat")
    out_path = tmp_path / "sv_savedata.dat"
    svsd.save(str(out_path))
    svsd2 = SummerVacationSaveData.load(str(out_path))
    assert svsd.meta["WorldName"] == svsd2.meta["WorldName"]
    assert len(svsd.charas) == len(svsd.chara_details) == len(svsd2.charas) == len(svsd2.chara_details)
    assert raw_data == bytes(svsd)
    assert bytes(svsd) == bytes(svsd2)


def test_savedata_load_invalid_type():
    with pytest.raises(ValueError, match="unsupported input"):
        KoikatuSaveData.load(123)


def test_aicomi_savedata(savedata_dir, tmp_path):
    save_path = savedata_dir / "ac_savedata.dat"
    with open(save_path, "rb") as f:
        raw_data = f.read()
    acs = AicomiSaveData.load(save_path)
    out_path = tmp_path / "ac_savedata.dat"
    acs.save(str(out_path))
    acs2 = AicomiSaveData.load(str(out_path))
    assert raw_data == bytes(acs)
    assert bytes(acs) == bytes(acs2)
    assert len(acs.charas) == 8
    assert acs.player["type"] == "PlayerData"
    assert acs.core["SaveTimeText"] == "2026/07/05 4:50:25"
    assert "相原 結里" in acs.names.values()
    favors = [npc["fields"]["FavorValue"] for npc in acs.npcs if npc is not None]
    assert favors == [0, 0, 0, 0]
    assert [unique["fields"]["FavorValue"] for unique in acs.uniques] == [0, 0, 0]
    assert [unique["index"] for unique in acs.uniques] == [0, 1, 2]


def test_aicomi_savedata_edit_chara(savedata_dir):
    save_path = savedata_dir / "ac_savedata.dat"
    with open(save_path, "rb") as f:
        raw_data = f.read()
    acs = AicomiSaveData.load(save_path)
    acs.player["chara"]["Parameter"]["firstname"] = "検証太郎"
    edited = bytes(acs)
    assert edited != raw_data
    reloaded = AicomiSaveData.load(edited)
    assert bytes(reloaded) == edited
    assert reloaded.player["chara"]["Parameter"]["firstname"] == "検証太郎"


def test_aicomi_savedata_edit_fields(savedata_dir):
    save_path = savedata_dir / "ac_savedata.dat"
    with open(save_path, "rb") as f:
        raw_data = f.read()
    acs = AicomiSaveData.load(save_path)
    npc_index, npc = next((i, n) for i, n in enumerate(acs.npcs) if n is not None)
    npc["fields"]["FavorValue"] = 555
    npc["fields"]["Intimacy"] = 88
    acs.core["SaveTimeText"] = "2026/01/01 00:00:00"
    edited = bytes(acs)
    assert edited != raw_data
    reloaded = AicomiSaveData.load(edited)
    fields = reloaded.npcs[npc_index]["fields"]
    assert fields["FavorValue"] == 555
    assert fields["Intimacy"] == 88
    assert reloaded.core["SaveTimeText"] == "2026/01/01 00:00:00"
    assert bytes(reloaded) == edited


def test_amanatsu_savedata(savedata_dir, tmp_path):
    save_path = savedata_dir / "al_savedata.dat"
    with open(save_path, "rb") as f:
        raw_data = f.read()
    als = AmanatsuSaveData.load(save_path)
    out_path = tmp_path / "al_savedata.dat"
    als.save(out_path)
    reloaded = AmanatsuSaveData.load(out_path)
    assert raw_data == bytes(als)
    assert bytes(reloaded) == raw_data
    assert len(als.npcs) == 30
    assert len(als.charas) == 4
    assert als.player["type"] == "PlayerData"
    assert als.core["SaveTimeText"] == "2026/09/18 6:23:49"
    assert "陣内 亮" in als.names.values()


def test_amanatsu_savedata_edit_chara(savedata_dir):
    save_path = savedata_dir / "al_savedata.dat"
    raw_data = save_path.read_bytes()
    als = AmanatsuSaveData.load(raw_data)
    als.player["chara"]["Parameter"]["firstname"] = "検証太郎"
    edited = bytes(als)
    assert edited != raw_data
    reloaded = AmanatsuSaveData.load(edited)
    assert bytes(reloaded) == edited
    assert reloaded.player["chara"]["Parameter"]["firstname"] == "検証太郎"


def test_amanatsu_savedata_edit_fields(savedata_dir):
    save_path = savedata_dir / "al_savedata.dat"
    raw_data = save_path.read_bytes()
    als = AmanatsuSaveData.load(raw_data)
    npc_index, npc = next((i, n) for i, n in enumerate(als.npcs) if n is not None)
    npc["fields"]["GameParameter"]["Favorability"]["Point"] = 555
    npc["fields"]["GameParameter"]["Favorability"]["LV"] = 3
    als.core["Comment"] = "roundtrip-test"
    edited = bytes(als)
    assert edited != raw_data
    reloaded = AmanatsuSaveData.load(edited)
    fields = reloaded.npcs[npc_index]["fields"]
    assert fields["GameParameter"]["Favorability"]["Point"] == 555
    assert fields["GameParameter"]["Favorability"]["LV"] == 3
    assert reloaded.core["Comment"] == "roundtrip-test"
    assert bytes(reloaded) == edited


# MemoryPack codec tests (no save-data fixture required)


@pytest.mark.parametrize("value", [None, "", "abc", "2026/03/31 17:01:53", "天宮 心音", "café"])
def test_memorypack_string_roundtrip(value):
    writer = MpWriter()
    writer.string(value)
    reader = MpReader(writer.bytes())
    assert reader.string() == value
    assert reader.pos == len(writer.bytes())


def test_memorypack_object_header():
    assert MpReader(b"\xff").object_header() is None
    assert MpReader(b"\x1d").object_header() == 29


def test_memorypack_version():
    blob = bytes([4]) + b"".join(v.to_bytes(4, "little") for v in (1, 2, 3, 4))
    assert read_version(MpReader(blob)) == {"major": 1, "minor": 2, "build": 3, "revision": 4}

    writer = MpWriter()
    write_version(writer, {"major": 1, "minor": 2, "build": 3, "revision": 4})
    assert writer.bytes() == blob


@pytest.mark.parametrize("value", [None, "0.0.0", "1.2.3.4"])
def test_memorypack_version_string_roundtrip(value):
    writer = MpWriter()
    write_version_string(writer, value)
    reader = MpReader(writer.bytes())
    assert read_version_string(reader) == value
    assert reader.pos == len(writer.bytes())


@pytest.mark.parametrize("value", [None, b"", b"\x00\xffabc"])
def test_memorypack_byte_array_roundtrip(value):
    writer = MpWriter()
    write_byte_array(writer, value)
    reader = MpReader(writer.bytes())
    assert read_byte_array(reader) == value
    assert reader.pos == len(writer.bytes())


@pytest.mark.parametrize("value", [None, [], [-1, 0, 42, 2**31 - 1]])
def test_memorypack_primitive_array_roundtrip(value):
    writer = MpWriter()
    write_primitive_array(writer, "int", value)
    reader = MpReader(writer.bytes())
    assert read_primitive_array(reader, "int") == value
    assert reader.pos == len(writer.bytes())


def test_memorypack_u64_roundtrip():
    writer = MpWriter()
    writer.u64(2**64 - 1)
    reader = MpReader(writer.bytes())
    assert reader.u64() == 2**64 - 1
