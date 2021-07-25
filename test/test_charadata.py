from kkloader import KoikatuCharaData


def test_load_character():
    kc = KoikatuCharaData.load("./data/kk_chara.png")
    assert hasattr(kc, "Custom")
    assert hasattr(kc, "Coordinate")
    assert hasattr(kc, "Parameter")
    assert hasattr(kc, "Status")


def test_load_sunshine_charater():
    kc = KoikatuCharaData.load("./data/kks_chara.png")
    assert hasattr(kc, "Custom")
    assert hasattr(kc, "Coordinate")
    assert hasattr(kc, "Parameter")
    assert hasattr(kc, "Status")
    assert hasattr(kc, "About")
