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
