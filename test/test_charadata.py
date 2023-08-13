import tempfile

from kkloader import EmocreCharaData, KoikatuCharaData, HoneycomeCharaData


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


def test_load_honeycome_character():
    hc = HoneycomeCharaData.load("./data/hc_chara.png")
    for f in hc.modules.keys():
        assert hasattr(hc, f)


def test_save_character():
    tmpfile = tempfile.NamedTemporaryFile()
    kc = KoikatuCharaData.load("./data/kk_chara.png")
    kc.save(tmpfile.name)
    kc2 = KoikatuCharaData.load(tmpfile.name)
    assert kc["Parameter"]["nickname"] == kc2["Parameter"]["nickname"]
    assert bytes(kc) == bytes(kc2)


def test_save_sunshine_character():
    tmpfile = tempfile.NamedTemporaryFile()
    kc = KoikatuCharaData.load("./data/kks_chara.png")
    kc.save(tmpfile.name)
    kc2 = KoikatuCharaData.load(tmpfile.name)
    assert kc["Parameter"]["nickname"] == kc2["Parameter"]["nickname"]
    assert bytes(kc) == bytes(kc2)


def test_save_emocre_character():
    tmpfile = tempfile.NamedTemporaryFile()
    ec = EmocreCharaData.load("./data/ec_chara.png")
    ec.save(tmpfile.name)
    ec2 = EmocreCharaData.load(tmpfile.name)
    assert ec["Parameter"]["fullname"] == ec2["Parameter"]["fullname"]
    assert bytes(ec) == bytes(ec2)


def test_save_honeycome_character():
    tmpfile = tempfile.NamedTemporaryFile()
    hc = HoneycomeCharaData.load("./data/hc_chara.png")
    hc.save(tmpfile.name)
    hc2 = HoneycomeCharaData.load(tmpfile.name)
    assert hc["Parameter"]["lastname"] == hc2["Parameter"]["lastname"]
    assert hc["Parameter"]["firstname"] == hc2["Parameter"]["firstname"]
    assert bytes(hc) == bytes(hc2)


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


def test_json_honeycome():
    hc = HoneycomeCharaData.load("./data/hc_chara.png")
    tmpfile = tempfile.NamedTemporaryFile()
    hc.save_json("test.json")
    hc.save_json(tmpfile.name)
