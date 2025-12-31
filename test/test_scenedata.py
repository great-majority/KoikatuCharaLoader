import tempfile

import pytest

from kkloader import KoikatuSceneData


def test_load_simple_scene():
    """Test loading a simple Koikatu scene file with one item"""
    # Load the scene data
    scene_data = KoikatuSceneData.load("./data/kk_scene_simple.png")

    # Check basic properties
    assert hasattr(scene_data, "version")
    assert hasattr(scene_data, "dicObject")
    assert hasattr(scene_data, "map")
    assert scene_data.version == "1.1.2.1"

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


def test_load_complex_scene():
    """Test loading a complex scene file with multiple object types"""
    # Load the scene data
    scene_data = KoikatuSceneData.load("./data/kk_scene.png")

    # Check basic properties
    assert hasattr(scene_data, "version")
    assert hasattr(scene_data, "dicObject")
    assert hasattr(scene_data, "map")
    assert scene_data.version == "0.0.7"

    # Check that the scene has 10 objects
    assert len(scene_data.dicObject) == 10

    # Check that we have the expected object types
    object_types = {obj["type"] for obj in scene_data.dicObject.values()}
    assert 0 in object_types  # Character
    assert 1 in object_types  # Item
    assert 2 in object_types  # Light

    # Count objects by type
    type_counts = {}
    for obj in scene_data.dicObject.values():
        obj_type = obj["type"]
        type_counts[obj_type] = type_counts.get(obj_type, 0) + 1

    assert type_counts[0] == 1  # 1 character
    assert type_counts[2] == 2  # 2 lights
    assert type_counts[1] == 7  # 7 items


def test_load_character_in_scene():
    """Test that character data is properly loaded in scene file"""
    scene_data = KoikatuSceneData.load("./data/kk_scene.png")

    # Find the character object (type 0)
    char_obj = None
    for obj in scene_data.dicObject.values():
        if obj["type"] == 0:
            char_obj = obj
            break

    assert char_obj is not None, "Character object not found"

    # Check character data structure
    char_data = char_obj["data"]
    assert "dicKey" in char_data
    assert "position" in char_data
    assert "rotation" in char_data
    assert "scale" in char_data
    assert "sex" in char_data
    assert "character" in char_data
    assert "bones" in char_data
    assert "ik_targets" in char_data
    assert "child" in char_data

    # Check that character file data was loaded
    assert hasattr(char_data["character"], "Custom")
    assert hasattr(char_data["character"], "Parameter")


def test_load_light_in_scene():
    """Test that light data is properly loaded in scene file"""
    scene_data = KoikatuSceneData.load("./data/kk_scene.png")

    # Find a light object (type 2)
    light_obj = None
    for obj in scene_data.dicObject.values():
        if obj["type"] == 2:
            light_obj = obj
            break

    assert light_obj is not None, "Light object not found"

    # Check light data structure
    light_data = light_obj["data"]
    assert "dicKey" in light_data
    assert "position" in light_data
    assert "rotation" in light_data
    assert "scale" in light_data
    assert "no" in light_data
    assert "color" in light_data
    assert "intensity" in light_data
    assert "range" in light_data
    assert "spotAngle" in light_data

    # Check color structure
    assert "r" in light_data["color"]
    assert "g" in light_data["color"]
    assert "b" in light_data["color"]
    assert "a" in light_data["color"]


def test_load_item_in_scene():
    """Test that item data is properly loaded in scene file"""
    scene_data = KoikatuSceneData.load("./data/kk_scene.png")

    # Find an item object (type 1)
    item_obj = None
    for obj in scene_data.dicObject.values():
        if obj["type"] == 1:
            item_obj = obj
            break

    assert item_obj is not None, "Item object not found"

    # Check item data structure
    item_data = item_obj["data"]
    assert "dicKey" in item_data
    assert "position" in item_data
    assert "rotation" in item_data
    assert "scale" in item_data
    assert "group" in item_data
    assert "category" in item_data
    assert "no" in item_data
    assert "colors" in item_data
    assert "patterns" in item_data
    assert "bones" in item_data
    assert "child" in item_data


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


@pytest.mark.skip(reason="Scene save functionality not fully implemented for complex scenes yet")
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
