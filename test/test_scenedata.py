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
