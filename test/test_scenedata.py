import tempfile

from kkloader import KoikatuSceneData


def test_load_scene():
    """Test loading a Koikatu scene file"""
    # Load the scene data
    scene_data = KoikatuSceneData.load("./data/kk_scene_simple.png")
    
    # Check basic properties
    assert hasattr(scene_data, "version")
    assert hasattr(scene_data, "dicObject")
    assert hasattr(scene_data, "map")
    
    # Check that the scene has exactly one object
    assert len(scene_data.dicObject) == 1
    
    # Check that the object is of the expected type (1 = OIItemInfo)
    obj_key = list(scene_data.dicObject.keys())[0]
    assert scene_data.dicObject[obj_key]["type"] == 1
    
    # Check that the object has the expected data structure
    obj_data = scene_data.dicObject[obj_key]["data"]
    assert "group" in obj_data
    assert "category" in obj_data
    assert "no" in obj_data
    assert "colors" in obj_data
    assert "patterns" in obj_data
    assert "panel" in obj_data


def test_scene_to_dict():
    """Test converting a scene to a dictionary"""
    scene_data = KoikatuSceneData.load("./data/kk_scene_simple.png")
    scene_dict = scene_data.to_dict()
    
    # Check that the dictionary has the expected keys
    assert "version" in scene_dict
    assert "map" in scene_dict
    assert "objectCount" in scene_dict
    
    # Check that the object count matches
    assert scene_dict["objectCount"] == len(scene_data.dicObject)


def test_save_scene():
    """Test saving a Koikatu scene file"""
    # Load the original scene data
    with open("./data/kk_scene_simple.png", "rb") as f:
        raw_data = f.read()
    
    # Load the scene data
    scene_data = KoikatuSceneData.load("./data/kk_scene_simple.png")
    
    # Save to a temporary file
    tmpfile = tempfile.NamedTemporaryFile()
    scene_data.save(tmpfile.name)
    
    # Load the saved scene data
    scene_data2 = KoikatuSceneData.load(tmpfile.name)
    
    # Check that the basic properties match
    assert scene_data.version == scene_data2.version
    assert scene_data.map == scene_data2.map
    assert len(scene_data.dicObject) == len(scene_data2.dicObject)
    
    # Check that the object data matches
    obj_key = list(scene_data.dicObject.keys())[0]
    obj_key2 = list(scene_data2.dicObject.keys())[0]
    
    assert scene_data.dicObject[obj_key]["type"] == scene_data2.dicObject[obj_key2]["type"]
    
    # Check that the serialized data matches
    assert len(raw_data) == len(bytes(scene_data))
    assert raw_data == bytes(scene_data)
    assert bytes(scene_data) == bytes(scene_data2)
