import tempfile

from kkloader import AmanatsuCharaData


def test_load_amanatsu_character():
    al = AmanatsuCharaData.load("./data/al_chara.png")
    assert hasattr(al, "Custom")
    assert hasattr(al, "Coordinate")
    assert hasattr(al, "Parameter")
    assert hasattr(al, "Status")
    assert hasattr(al, "Graphic")
    assert hasattr(al, "About")
    assert hasattr(al, "GameParameter_AL")
    assert hasattr(al, "GameInfo_AL")
    assert hasattr(al, "ThumbParameter")
    for b in al.blockdata:
        assert b in al.modules.keys()


def test_load_amanatsu_coordinate_structure():
    al = AmanatsuCharaData.load("./data/al_chara.png")
    coord = al["Coordinate"]
    assert len(coord.data) == 2
    for entry in coord.data:
        assert "Clothes" in entry.blockdata
        assert "Accessory" in entry.blockdata
        assert "Hair" in entry.blockdata
        assert "FaceMakeup" in entry.blockdata
        assert "BodyMakeup" in entry.blockdata
        assert "About" in entry.blockdata


def test_save_amanatsu_character():
    with open("./data/al_chara.png", "rb") as f:
        raw_data = f.read()
    tmpfile = tempfile.NamedTemporaryFile()
    al = AmanatsuCharaData.load("./data/al_chara.png")
    al.save(tmpfile.name)
    al2 = AmanatsuCharaData.load(tmpfile.name)
    assert al["Parameter"]["lastname"] == al2["Parameter"]["lastname"]
    assert al["Parameter"]["firstname"] == al2["Parameter"]["firstname"]
    assert raw_data == bytes(al)
    assert bytes(al) == bytes(al2)


def test_json_amanatsu():
    al = AmanatsuCharaData.load("./data/al_chara.png")
    tmpfile = tempfile.NamedTemporaryFile()
    al.save_json(tmpfile.name)


def test_repr_amanatsu():
    al = AmanatsuCharaData.load("./data/al_chara.png")
    repr_text = repr(al)
    assert "AmanatsuCharaData" in repr_text
    assert "【ALChara】" in repr_text


def test_load_al_coordinate():
    from kkloader.AmanatsuCharaData import CoordinateEntry

    entry = CoordinateEntry.load("./data/al_coordinate.png", contains_png=True)
    assert entry.image is not None
    assert entry.header == b"\xe3\x80\x90ALClothes\xe3\x80\x91"
    assert entry.product_no == 100
    assert entry.blockdata == ["Clothes", "Accessory", "Hair", "FaceMakeup", "BodyMakeup", "About"]
    assert entry.original_file_path.endswith("al_coordinate.png")


def test_save_al_coordinate():
    from kkloader.AmanatsuCharaData import CoordinateEntry

    with open("./data/al_coordinate.png", "rb") as f:
        raw_data = f.read()
    entry = CoordinateEntry.load("./data/al_coordinate.png", contains_png=True)
    tmpfile = tempfile.NamedTemporaryFile()
    entry.save(tmpfile.name)
    with open(tmpfile.name, "rb") as f:
        saved_data = f.read()
    assert raw_data == saved_data
