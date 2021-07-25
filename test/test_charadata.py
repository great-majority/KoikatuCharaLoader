import tempfile

from kkloader import EmocreCharaData, KoikatuCharaData


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
