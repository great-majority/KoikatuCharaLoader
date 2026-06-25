import tempfile

from kkloader.EmocreSceneData import EmocreSceneData


def test_load_emocre_scene():
    scene = EmocreSceneData.load("./data/ec_scene.png")
    assert scene.header == "【EroMakeHScene】"
    assert scene.product_no == 200
    assert len(scene.charas) > 0
    assert len(scene.maps) > 0
    assert len(scene.parts) > 0
    assert scene.node_graph is not None
    assert len(scene.node_graph.nodes) > 0


def test_save_emocre_scene():
    with open("./data/ec_scene.png", "rb") as f:
        raw_data = f.read()
    scene = EmocreSceneData.load("./data/ec_scene.png")
    tmpfile = tempfile.NamedTemporaryFile()
    scene.save(tmpfile.name)
    scene2 = EmocreSceneData.load(tmpfile.name)
    assert scene.info["title"] == scene2.info["title"]
    assert raw_data == bytes(scene)
    assert bytes(scene) == bytes(scene2)
