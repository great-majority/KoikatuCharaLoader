import os
import tempfile
from pathlib import Path

from kkloader import (
    AicomiCharaData,
    EmocreCharaData,
    HoneycomeCharaData,
    KoikatuCharaData,
    SummerVacationCharaData,
)

import pytest


def test_load_character():
    kc = KoikatuCharaData.load("./data/kk_chara.png")
    assert hasattr(kc, "Custom")
    assert hasattr(kc, "Coordinate")
    assert hasattr(kc, "Parameter")
    assert hasattr(kc, "Status")
    assert kc.original_file_path == os.path.abspath("./data/kk_chara.png")


def test_load_character_from_bytes_has_no_original_file_path():
    with open("./data/kk_chara.png", "rb") as f:
        raw_data = f.read()
    kc = KoikatuCharaData.load(raw_data)
    assert kc.original_file_path is None


def test_load_sunshine_character():
    kc = KoikatuCharaData.load("./data/kks_chara.png")
    assert hasattr(kc, "Custom")
    assert hasattr(kc, "Coordinate")
    assert hasattr(kc, "Parameter")
    assert hasattr(kc, "Status")
    assert hasattr(kc, "About")


def test_load_emocre_character():
    ec = EmocreCharaData.load("./data/ec_chara.png")
    assert hasattr(ec, "Custom")
    assert hasattr(ec, "Coordinate")
    assert hasattr(ec, "Parameter")
    assert hasattr(ec, "Status")


def test_load_mod_character():
    kc = KoikatuCharaData.load("./data/kk_mod_chara.png")
    assert hasattr(kc, "Custom")
    assert hasattr(kc, "Coordinate")
    assert hasattr(kc, "Parameter")
    assert hasattr(kc, "Status")
    assert hasattr(kc, "KKEx")


def test_load_honeycome_party_character():
    hc = HoneycomeCharaData.load("./data/hcp_chara.png")
    for b in hc.blockdata:
        assert b in hc.modules.keys()


def test_load_honeycome_character():
    hc = HoneycomeCharaData.load("./data/hc_chara.png")
    for b in hc.blockdata:
        assert b in hc.modules.keys()


def test_load_summervacation_character():
    svc = SummerVacationCharaData.load("./data/sv_chara.png")
    for b in svc.blockdata:
        assert b in svc.modules.keys()


def test_load_aicomi_character():
    ac = AicomiCharaData.load("./data/ac_chara.png")
    for b in ac.blockdata:
        assert b in ac.modules.keys()


def test_save_character():
    with open("./data/kk_chara.png", "rb") as f:
        raw_data = f.read()
    tmpfile = tempfile.NamedTemporaryFile()
    kc = KoikatuCharaData.load("./data/kk_chara.png")
    kc.save(tmpfile.name)
    kc2 = KoikatuCharaData.load(tmpfile.name)
    assert kc["Parameter"]["nickname"] == kc2["Parameter"]["nickname"]
    assert raw_data == bytes(kc)
    assert bytes(kc) == bytes(kc2)


def test_save_sunshine_character():
    with open("./data/kks_chara.png", "rb") as f:
        raw_data = f.read()
    tmpfile = tempfile.NamedTemporaryFile()
    kc = KoikatuCharaData.load("./data/kks_chara.png")
    kc.save(tmpfile.name)
    kc2 = KoikatuCharaData.load(tmpfile.name)
    assert kc["Parameter"]["nickname"] == kc2["Parameter"]["nickname"]
    assert raw_data == bytes(kc)
    assert bytes(kc) == bytes(kc2)


def test_save_modding_character():
    with open("./data/kk_mod_chara.png", "rb") as f:
        raw_data = f.read()
    tmpfile = tempfile.NamedTemporaryFile()
    kc = KoikatuCharaData.load("./data/kk_mod_chara.png")
    kc.save(tmpfile.name)
    kc2 = KoikatuCharaData.load(tmpfile.name)
    assert kc["Parameter"]["nickname"] == kc2["Parameter"]["nickname"]
    assert bytes(kc) == bytes(kc2)
    assert raw_data == bytes(kc)
    assert raw_data == bytes(kc2)


@pytest.mark.parametrize("chara_path", [str(p) for p in Path("./data/testing-data").glob("*.png")])
def test_save_modding_character_param(chara_path, request):
    if not request.config.getoption("--run-optional"):
        pytest.skip("requires `--run-optional` to run")

    print("=" * 20)
    print(f"Testing {chara_path}")
    with open(chara_path, "rb") as f:
        raw_data = f.read()

    tmpfile = tempfile.NamedTemporaryFile(delete=False)
    try:
        kc = KoikatuCharaData.load(chara_path)
        kc.save(tmpfile.name)
        kc2 = KoikatuCharaData.load(tmpfile.name)

        assert kc["Parameter"]["nickname"] == kc2["Parameter"]["nickname"]
        assert bytes(kc) == bytes(kc2)
        assert raw_data == bytes(kc)
        assert raw_data == bytes(kc2)

    finally:
        tmpfile.close()
        os.unlink(tmpfile.name)


def test_save_emocre_character():
    with open("./data/ec_chara.png", "rb") as f:
        raw_data = f.read()
    tmpfile = tempfile.NamedTemporaryFile()
    ec = EmocreCharaData.load("./data/ec_chara.png")
    ec.save(tmpfile.name)
    ec2 = EmocreCharaData.load(tmpfile.name)
    assert ec["Parameter"]["fullname"] == ec2["Parameter"]["fullname"]
    assert raw_data == bytes(ec)
    assert bytes(ec) == bytes(ec2)


def test_save_honeycome_party_character():
    with open("./data/hcp_chara.png", "rb") as f:
        raw_data = f.read()
    tmpfile = tempfile.NamedTemporaryFile()
    hc = HoneycomeCharaData.load("./data/hcp_chara.png")
    hc.save(tmpfile.name)
    hc2 = HoneycomeCharaData.load(tmpfile.name)
    assert hc["Parameter"]["lastname"] == hc2["Parameter"]["lastname"]
    assert hc["Parameter"]["firstname"] == hc2["Parameter"]["firstname"]
    assert raw_data == bytes(hc)
    assert bytes(hc) == bytes(hc2)


def test_save_honeycome_character():
    with open("./data/hc_chara.png", "rb") as f:
        raw_data = f.read()
    tmpfile = tempfile.NamedTemporaryFile()
    hc = HoneycomeCharaData.load("./data/hc_chara.png")
    hc.save(tmpfile.name)
    hc2 = HoneycomeCharaData.load(tmpfile.name)
    assert hc["Parameter"]["lastname"] == hc2["Parameter"]["lastname"]
    assert hc["Parameter"]["firstname"] == hc2["Parameter"]["firstname"]
    assert raw_data == bytes(hc)
    assert bytes(hc) == bytes(hc2)


def test_save_summervacation_character():
    with open("./data/sv_chara.png", "rb") as f:
        raw_data = f.read()
    tmpfile = tempfile.NamedTemporaryFile()
    svc = SummerVacationCharaData.load("./data/sv_chara.png")
    svc.save(tmpfile.name)
    svc2 = SummerVacationCharaData.load(tmpfile.name)
    assert svc["Parameter"]["lastname"] == svc2["Parameter"]["lastname"]
    assert svc["Parameter"]["firstname"] == svc2["Parameter"]["firstname"]
    assert raw_data == bytes(svc)
    assert bytes(svc) == bytes(svc2)


def test_save_aicomi_character():
    with open("./data/ac_chara.png", "rb") as f:
        raw_data = f.read()
    tmpfile = tempfile.NamedTemporaryFile()
    ac = AicomiCharaData.load("./data/ac_chara.png")
    ac.save(tmpfile.name)
    ac2 = AicomiCharaData.load(tmpfile.name)
    assert ac["Parameter"]["lastname"] == ac2["Parameter"]["lastname"]
    assert ac["Parameter"]["firstname"] == ac2["Parameter"]["firstname"]
    assert raw_data == bytes(ac)
    assert bytes(ac) == bytes(ac2)


def test_json_character():
    kc = KoikatuCharaData.load("./data/kk_chara.png")
    tmpfile = tempfile.NamedTemporaryFile()
    kc.save_json(tmpfile.name)


def test_json_sunshine_character():
    kc = KoikatuCharaData.load("./data/kks_chara.png")
    tmpfile = tempfile.NamedTemporaryFile()
    kc.save_json(tmpfile.name)


def test_json_emocre_character():
    ec = EmocreCharaData.load("./data/ec_chara.png")
    tmpfile = tempfile.NamedTemporaryFile()
    ec.save_json(tmpfile.name)


def test_json_honeycome_party():
    hc = HoneycomeCharaData.load("./data/hcp_chara.png")
    tmpfile = tempfile.NamedTemporaryFile()
    hc.save_json(tmpfile.name)


def test_json_honeycome():
    hc = HoneycomeCharaData.load("./data/hc_chara.png")
    tmpfile = tempfile.NamedTemporaryFile()
    hc.save_json(tmpfile.name)


def test_json_summervacation():
    hc = SummerVacationCharaData.load("./data/sv_chara.png")
    tmpfile = tempfile.NamedTemporaryFile()
    hc.save_json(tmpfile.name)


def test_json_aicomi():
    ac = AicomiCharaData.load("./data/ac_chara.png")
    tmpfile = tempfile.NamedTemporaryFile()
    ac.save_json(tmpfile.name)


def _assert_common_repr_fields(chara_data, expected_name):
    repr_text = repr(chara_data)
    assert f"product_no={chara_data.product_no!r}" in repr_text
    assert f"header={chara_data.header.decode('utf-8')!r}" in repr_text
    assert f"version={chara_data.version.decode('utf-8')!r}" in repr_text
    assert f"name={expected_name!r}" in repr_text
    assert f"blocks={chara_data.blockdata!r}" in repr_text
    assert f"has_kkex={'KKEx' in chara_data.blockdata}" in repr_text
    assert f"original_file_path={chara_data.original_file_path!r}" in repr_text


def _expected_repr_name(chara_data):
    param = chara_data["Parameter"].data
    fullname = str(param.get("fullname", "")).strip()
    if fullname:
        return fullname
    lastname = str(param.get("lastname", "")).strip()
    firstname = str(param.get("firstname", "")).strip()
    nickname = str(param.get("nickname", "")).strip()
    name = "{} {}".format(lastname, firstname).strip()
    if nickname:
        return "{} ( {} )".format(name, nickname).strip()
    return name


def test_repr_koikatu_fields():
    kc = KoikatuCharaData.load("./data/kk_chara.png")
    expected_name = _expected_repr_name(kc)
    _assert_common_repr_fields(kc, expected_name)


def test_repr_mod_character_has_kkex():
    kc = KoikatuCharaData.load("./data/kk_mod_chara.png")
    assert "has_kkex=True" in repr(kc)


def test_repr_emocre_name():
    ec = EmocreCharaData.load("./data/ec_chara.png")
    expected_name = _expected_repr_name(ec)
    _assert_common_repr_fields(ec, expected_name)
    repr_text = repr(ec)
    assert f"userid={ec.userid.decode('utf-8')!r}" in repr_text
    assert f"dataid={ec.dataid.decode('utf-8')!r}" in repr_text


def test_repr_sunshine_contains_about_guids():
    kks = KoikatuCharaData.load("./data/kks_chara.png")
    repr_text = repr(kks)
    assert f"userid={kks['About']['userID']!r}" in repr_text
    assert f"dataid={kks['About']['dataID']!r}" in repr_text


def test_repr_honeycome_like_name_and_about_guids():
    for cls, path in [
        (HoneycomeCharaData, "./data/hc_chara.png"),
        (SummerVacationCharaData, "./data/sv_chara.png"),
        (AicomiCharaData, "./data/ac_chara.png"),
    ]:
        chara = cls.load(path)
        repr_text = repr(chara)
        expected_name = _expected_repr_name(chara)
        _assert_common_repr_fields(chara, expected_name)
        assert f"userid={chara['About']['userID']!r}" in repr_text
        assert f"dataid={chara['About']['dataID']!r}" in repr_text


def test_character_str_falls_back_to_repr():
    samples = [
        KoikatuCharaData.load("./data/kk_chara.png"),
        EmocreCharaData.load("./data/ec_chara.png"),
        HoneycomeCharaData.load("./data/hc_chara.png"),
        SummerVacationCharaData.load("./data/sv_chara.png"),
        AicomiCharaData.load("./data/ac_chara.png"),
    ]
    for chara in samples:
        assert str(chara) == repr(chara)
