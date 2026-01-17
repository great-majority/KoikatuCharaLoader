import tempfile

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


def count_types_recursive(dicObject):
    """Recursively count all objects by type including nested children"""
    type_counts = {}
    for obj in dicObject.values():
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

    type_counts = count_types_recursive(scene_data.dicObject)
    # type: 0=Character, 1=Item, 2=Light, 3=Folder
    assert type_counts.get(0, 0) == 1  # 1 character
    assert type_counts.get(1, 0) == 169  # 169 items
    assert type_counts.get(3, 0) == 19  # 19 folders


def test_load_kks_scene():
    """Test loading kks_scene.png (Koikatsu Sunshine)"""
    scene_data = KoikatuSceneData.load("./data/kks_scene.png")
    assert scene_data.version == "1.1.2.1"

    type_counts = count_types_recursive(scene_data.dicObject)
    assert type_counts.get(2, 0) == 1  # 1 light
    assert type_counts.get(3, 0) == 1  # 1 folder


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


def count_all_objects(dicObject):
    """Recursively count all objects including nested children"""
    count = len(dicObject)
    for obj in dicObject.values():
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
    assert len(scene_data.dicObject) == len(scene_data2.dicObject)

    # Check total object count including nested objects
    total_count_1 = count_all_objects(scene_data.dicObject)
    total_count_2 = count_all_objects(scene_data2.dicObject)
    assert total_count_1 == total_count_2, f"Total object count mismatch: {total_count_1} vs {total_count_2}"

    # Check that the object data matches
    obj_key = list(scene_data.dicObject.keys())[0]
    obj_key2 = list(scene_data2.dicObject.keys())[0]

    assert scene_data.dicObject[obj_key]["type"] == scene_data2.dicObject[obj_key2]["type"]

    # Check that all object data is preserved through save/load cycle
    for key in scene_data.dicObject.keys():
        obj1 = scene_data.dicObject[key]
        obj2 = scene_data2.dicObject[key]

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

    type_counts1 = count_types_recursive(scene_data.dicObject)
    type_counts2 = count_types_recursive(scene_data2.dicObject)
    assert type_counts1 == type_counts2


def test_save_kks_scene():
    """Test saving kks_scene.png (Koikatsu Sunshine)"""
    scene_data = KoikatuSceneData.load("./data/kks_scene.png")

    tmpfile = tempfile.NamedTemporaryFile()
    scene_data.save(tmpfile.name)

    scene_data2 = KoikatuSceneData.load(tmpfile.name)

    type_counts1 = count_types_recursive(scene_data.dicObject)
    type_counts2 = count_types_recursive(scene_data2.dicObject)
    assert type_counts1 == type_counts2
