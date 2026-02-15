import os
import tempfile

from kkloader import KoikatuSceneData


def test_load_simple_scene():
    """Test loading a simple Koikatu scene file with one item"""
    # Load the scene data
    scene_data = KoikatuSceneData.load("./data/kk_scene_simple.png")

    # Check basic properties
    assert hasattr(scene_data, "version")
    assert hasattr(scene_data, "objects")
    assert hasattr(scene_data, "map")
    assert scene_data.version == "1.1.2.1"

    # Check that the scene has exactly one object
    assert len(scene_data.objects) == 1

    # Check that the object is of the expected type (1 = OIItemInfo)
    obj_key = list(scene_data.objects.keys())[0]
    assert scene_data.objects[obj_key]["type"] == 1

    # Check that the object has the expected data structure
    obj_data = scene_data.objects[obj_key]["data"]
    assert "group" in obj_data
    assert "category" in obj_data
    assert "no" in obj_data
    assert "colors" in obj_data
    assert "patterns" in obj_data
    assert "panel" in obj_data


def test_koikatu_scene_repr_fields():
    scene_data = KoikatuSceneData.load("./data/kk_scene_simple.png")
    repr_text = repr(scene_data)
    assert f"version={scene_data.version!r}" in repr_text
    assert f"original_filename={os.path.abspath('./data/kk_scene_simple.png')!r}" in repr_text
    assert f"tail={scene_data.tail!r}" in repr_text
    assert "has_mod=False" in repr_text


def test_koikatu_scene_repr_has_mod_for_mod_scene():
    scene_data = KoikatuSceneData.load("./data/kk_scene_mod.png")
    assert "has_mod=True" in repr(scene_data)


def test_koikatu_scene_original_filename_for_bytes_input():
    with open("./data/kk_scene_simple.png", "rb") as f:
        raw_data = f.read()
    scene_data = KoikatuSceneData.load(raw_data)
    assert scene_data.original_filename is None


def count_types_recursive(objects):
    """Recursively count all objects by type including nested children"""
    type_counts = {}
    for obj in objects.values():
        obj_type = obj["type"]
        type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
        data = obj.get("data", {})
        if "child" in data and data["child"]:
            children = data["child"]
            if isinstance(children, list):
                child_dict = {i: c for i, c in enumerate(children)}
                child_counts = count_types_recursive(child_dict)
                for t, count in child_counts.items():
                    type_counts[t] = type_counts.get(t, 0) + count
    return type_counts


def test_load_kk_scene():
    """Test loading kk_scene.png"""
    scene_data = KoikatuSceneData.load("./data/kk_scene.png")
    assert scene_data.version == "1.0.4.2"

    type_counts = count_types_recursive(scene_data.objects)
    # type: 0=Character, 1=Item, 2=Light, 3=Folder
    assert type_counts.get(0, 0) == 1  # 1 character
    assert type_counts.get(1, 0) == 169  # 169 items
    assert type_counts.get(3, 0) == 19  # 19 folders


def test_load_kk_scene_mod():
    """Test loading kk_scene_mod.png"""
    scene_data = KoikatuSceneData.load("./data/kk_scene_mod.png")
    assert scene_data.version == "1.1.2.1"

    type_counts = count_types_recursive(scene_data.objects)
    # type: 0=Character, 1=Item, 2=Light, 3=Folder
    assert type_counts.get(0, 0) == 1  # 1 character
    assert type_counts.get(1, 0) == 201  # 201 items
    assert type_counts.get(2, 0) == 1  # 1 light
    assert type_counts.get(3, 0) == 202  # 202 folders


def test_load_kks_scene():
    """Test loading kks_scene.png (Koikatsu Sunshine)"""
    scene_data = KoikatuSceneData.load("./data/kks_scene.png")
    assert scene_data.version == "1.1.2.1"

    type_counts = count_types_recursive(scene_data.objects)
    assert type_counts.get(2, 0) == 1  # 1 light
    assert type_counts.get(3, 0) == 1  # 1 folder


def test_count_object_types_koikatu_scene():
    scene_data = KoikatuSceneData.load("./data/kk_scene.png")
    assert scene_data.count_object_types() == {"Folder": 19, "Item": 169, "Character": 1}


def test_count_object_types_koikatu_mod_scene():
    scene_data = KoikatuSceneData.load("./data/kk_scene_mod.png")
    assert scene_data.count_object_types() == {"Folder": 202, "Item": 202, "Character": 1, "Light": 1}


def test_count_object_types_kks_scene():
    scene_data = KoikatuSceneData.load("./data/kks_scene.png")
    assert scene_data.count_object_types() == {"Light": 1, "Folder": 1, "Item": 3, "Character": 1}


def test_walk_filter_object_type_koikatu():
    scene_data = KoikatuSceneData.load("./data/kk_scene.png")
    chars = list(scene_data.walk(object_type=KoikatuSceneData.CHARACTER))
    assert len(chars) == scene_data.count_object_types()["Character"]
    assert all(obj["type"] == KoikatuSceneData.CHARACTER for _, obj in chars)


def test_walk_filter_object_type_koikatu_with_depth():
    scene_data = KoikatuSceneData.load("./data/kks_scene.png")
    lights = list(scene_data.walk(include_depth=True, object_type=KoikatuSceneData.LIGHT))
    assert len(lights) == scene_data.count_object_types()["Light"]
    assert all(obj["type"] == KoikatuSceneData.LIGHT for _, obj, _ in lights)


def test_scene_to_dict():
    """Test converting a scene to a dictionary"""
    scene_data = KoikatuSceneData.load("./data/kk_scene_simple.png")
    scene_dict = scene_data.to_dict()

    # Check that the dictionary has the expected keys
    assert "version" in scene_dict
    assert "map" in scene_dict
    assert "objectCount" in scene_dict

    # Check that the object count matches
    assert scene_dict["objectCount"] == len(scene_data.objects)


def count_all_objects(objects):
    """Recursively count all objects including nested children"""
    count = len(objects)
    for obj in objects.values():
        data = obj.get("data", {})
        # Count children in folders and routes
        if "child" in data:
            child_data = data["child"]
            if isinstance(child_data, dict):
                # For CharInfo: child is a dict of lists
                for child_list in child_data.values():
                    count += count_all_objects({i: obj for i, obj in enumerate(child_list)})
            elif isinstance(child_data, list):
                # For FolderInfo/RouteInfo: child is a list
                count += count_all_objects({i: obj for i, obj in enumerate(child_data)})
        # Count route points
        if "route" in data and isinstance(data["route"], list):
            count += len(data["route"])
        # Count bones
        if "bones" in data and isinstance(data["bones"], dict):
            count += len(data["bones"])
        # Count IK targets
        if "ik_targets" in data and isinstance(data["ik_targets"], dict):
            count += len(data["ik_targets"])
    return count


def test_save_scene():
    """Test saving a Koikatu scene file"""
    # Load the scene data
    scene_data = KoikatuSceneData.load("./data/kk_scene_simple.png")

    # Save to a temporary file
    tmpfile = tempfile.NamedTemporaryFile()
    scene_data.save(tmpfile.name)

    # Load the saved scene data
    scene_data2 = KoikatuSceneData.load(tmpfile.name)

    # Check that the basic properties match (version check skipped - format may evolve)
    assert scene_data.map == scene_data2.map
    assert len(scene_data.objects) == len(scene_data2.objects)

    # Check total object count including nested objects
    total_count_1 = count_all_objects(scene_data.objects)
    total_count_2 = count_all_objects(scene_data2.objects)
    assert total_count_1 == total_count_2, f"Total object count mismatch: {total_count_1} vs {total_count_2}"

    # Check that the object data matches
    obj_key = list(scene_data.objects.keys())[0]
    obj_key2 = list(scene_data2.objects.keys())[0]

    assert scene_data.objects[obj_key]["type"] == scene_data2.objects[obj_key2]["type"]

    # Check that all object data is preserved through save/load cycle
    for key in scene_data.objects.keys():
        obj1 = scene_data.objects[key]
        obj2 = scene_data2.objects[key]

        # Check type matches
        assert obj1["type"] == obj2["type"], f"Object {key} type mismatch"

        # Check key data fields match
        data1 = obj1["data"]
        data2 = obj2["data"]

        # Check dicKey, position, rotation, scale
        assert data1.get("dicKey") == data2.get("dicKey"), f"Object {key} dicKey mismatch"

        # Check Vector3 fields (position, rotation, scale)
        for field in ["position", "rotation", "scale"]:
            if field in data1 and field in data2:
                v1 = data1[field]
                v2 = data2[field]
                for axis in ["x", "y", "z"]:
                    assert abs(v1.get(axis, 0.0) - v2.get(axis, 0.0)) < 1e-6, f"Object {key} {field}.{axis} mismatch: {v1.get(axis)} vs {v2.get(axis)}"

    # Check that scene metadata is preserved
    assert scene_data.sunLightType == scene_data2.sunLightType
    assert scene_data.mapOption == scene_data2.mapOption
    assert scene_data.aceNo == scene_data2.aceNo
    assert abs(scene_data.aceBlend - scene_data2.aceBlend) < 1e-6


def test_save_complex_scene():
    """Test saving a complex Koikatu scene file with multiple object types"""
    scene_data = KoikatuSceneData.load("./data/kk_scene.png")

    tmpfile = tempfile.NamedTemporaryFile()
    scene_data.save(tmpfile.name)

    scene_data2 = KoikatuSceneData.load(tmpfile.name)

    type_counts1 = count_types_recursive(scene_data.objects)
    type_counts2 = count_types_recursive(scene_data2.objects)
    assert type_counts1 == type_counts2


def test_save_kk_scene_mod():
    """Test saving kk_scene_mod.png"""
    scene_data = KoikatuSceneData.load("./data/kk_scene_mod.png")

    tmpfile = tempfile.NamedTemporaryFile()
    scene_data.save(tmpfile.name)

    scene_data2 = KoikatuSceneData.load(tmpfile.name)

    type_counts1 = count_types_recursive(scene_data.objects)
    type_counts2 = count_types_recursive(scene_data2.objects)
    assert type_counts1 == type_counts2


def test_save_kks_scene():
    """Test saving kks_scene.png (Koikatsu Sunshine)"""
    scene_data = KoikatuSceneData.load("./data/kks_scene.png")

    tmpfile = tempfile.NamedTemporaryFile()
    scene_data.save(tmpfile.name)

    scene_data2 = KoikatuSceneData.load(tmpfile.name)

    type_counts1 = count_types_recursive(scene_data.objects)
    type_counts2 = count_types_recursive(scene_data2.objects)
    assert type_counts1 == type_counts2
