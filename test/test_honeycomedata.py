import io
import os
import tempfile

from kkloader import HoneycomeSceneData


def test_load_honeycome_scene_items():
    """Test loading a Honeycome scene file"""
    scene_data = HoneycomeSceneData.load("./data/hc_scene_items.png")

    assert hasattr(scene_data, "version")
    assert hasattr(scene_data, "objects")
    assert hasattr(scene_data, "user_id")
    assert hasattr(scene_data, "data_id")
    assert hasattr(scene_data, "title")

    assert len(scene_data.objects) > 0

    has_folder = any(obj["type"] == 3 for obj in scene_data.objects.values())
    assert has_folder, "Expected at least one folder object in hc_scene_items.png"


def test_honeycome_scene_repr_fields():
    scene_data = HoneycomeSceneData.load("./data/hc_scene_items.png")
    repr_text = repr(scene_data)

    assert f"version={scene_data.version!r}" in repr_text
    assert f"title={scene_data.title!r}" in repr_text
    assert f"user_id={scene_data.user_id!r}" in repr_text
    assert f"data_id={scene_data.data_id!r}" in repr_text
    assert f"original_filename={os.path.abspath('./data/hc_scene_items.png')!r}" in repr_text
    assert f"footer_marker={scene_data.footer_marker!r}" in repr_text


def test_honeycome_scene_original_filename_for_bytes_input():
    with open("./data/hc_scene_items.png", "rb") as f:
        raw_data = f.read()
    scene_data = HoneycomeSceneData.load(raw_data)
    assert scene_data.original_filename is None


def test_honeycome_scene_to_dict():
    """Test converting a Honeycome scene to a dictionary"""
    scene_data = HoneycomeSceneData.load("./data/hc_scene_items.png")
    scene_dict = scene_data.to_dict()

    assert "version" in scene_dict
    assert "user_id" in scene_dict
    assert "data_id" in scene_dict
    assert "title" in scene_dict
    assert "objectCount" in scene_dict

    assert scene_dict["objectCount"] == len(scene_data.objects)


def test_save_honeycome_scene_roundtrip():
    """
    Test that saving and reloading hc_scene_items.png preserves all important instance variables.
    """
    scene_data_1 = HoneycomeSceneData.load("./data/hc_scene_items.png")

    output_stream = io.BytesIO()
    scene_data_1.save(output_stream)

    output_stream.seek(0)
    scene_data_2 = HoneycomeSceneData.load(output_stream)

    assert scene_data_1.version == scene_data_2.version, "Version mismatch"
    assert scene_data_1.dataVersion == scene_data_2.dataVersion, "Data version mismatch"
    assert scene_data_1.user_id == scene_data_2.user_id, "User ID mismatch"
    assert scene_data_1.data_id == scene_data_2.data_id, "Data ID mismatch"
    assert scene_data_1.title == scene_data_2.title, "Title mismatch"
    assert scene_data_1.unknown_1 == scene_data_2.unknown_1, "Unknown 1 mismatch"
    assert scene_data_1.unknown_2 == scene_data_2.unknown_2, "Unknown 2 mismatch"
    assert len(scene_data_1.objects) == len(scene_data_2.objects), "Object count mismatch"
    assert scene_data_1.unknown_tail == scene_data_2.unknown_tail, "Unknown tail mismatch"
    assert scene_data_1.footer_marker == scene_data_2.footer_marker, "Footer marker mismatch"
    assert scene_data_1.unknown_tail_extra is None

    assert set(scene_data_1.objects.keys()) == set(scene_data_2.objects.keys()), "Object keys mismatch"

    for key in scene_data_1.objects.keys():
        obj1 = scene_data_1.objects[key]
        obj2 = scene_data_2.objects[key]

        assert obj1["type"] == obj2["type"], f"Object {key} type mismatch"

        data1 = obj1["data"]
        data2 = obj2["data"]

        assert data1.get("dicKey") == data2.get("dicKey"), f"Object {key} dicKey mismatch"
        assert data1.get("treeState") == data2.get("treeState"), f"Object {key} treeState mismatch"
        assert data1.get("visible") == data2.get("visible"), f"Object {key} visible mismatch"

        for field in ["position", "rotation", "scale"]:
            if field in data1 and field in data2:
                v1 = data1[field]
                v2 = data2[field]
                for axis in ["x", "y", "z"]:
                    assert abs(v1.get(axis, 0.0) - v2.get(axis, 0.0)) < 1e-6, f"Object {key} {field}.{axis} mismatch"

        if obj1["type"] == 1:  # Item
            assert data1.get("group") == data2.get("group"), f"Item {key} group mismatch"
            assert data1.get("category") == data2.get("category"), f"Item {key} category mismatch"
            assert data1.get("no") == data2.get("no"), f"Item {key} no mismatch"

        elif obj1["type"] == 3:  # Folder
            assert data1.get("name") == data2.get("name"), f"Folder {key} name mismatch"
            assert len(data1.get("child", [])) == len(data2.get("child", [])), f"Folder {key} child count mismatch"


def test_save_honeycome_scene_binary_exact():
    """
    Test that saving and reloading hc_scene_items.png preserves the binary data exactly.
    """
    with open("./data/hc_scene_items.png", "rb") as f:
        original_bytes = f.read()

    scene_data = HoneycomeSceneData.load("./data/hc_scene_items.png")

    output_stream = io.BytesIO()
    scene_data.save(output_stream)
    saved_bytes = output_stream.getvalue()

    assert len(original_bytes) == len(saved_bytes), f"File size mismatch: {len(original_bytes)} vs {len(saved_bytes)}"
    assert original_bytes == saved_bytes, "Saved file is not byte-for-byte identical to original"


def test_item_data_preservation():
    """Test that item-specific data is preserved through save/load cycle"""
    scene_data = HoneycomeSceneData.load("./data/hc_scene_items.png")

    item_obj = None
    item_key = None
    for key, obj in scene_data.objects.items():
        if obj["type"] == 1:
            item_obj = obj
            item_key = key
            break

    if item_obj is None:
        return

    tmpfile = tempfile.NamedTemporaryFile(delete=False)
    scene_data.save(tmpfile.name)
    scene_data2 = HoneycomeSceneData.load(tmpfile.name)

    item_obj2 = scene_data2.objects[item_key]

    data1 = item_obj["data"]
    data2 = item_obj2["data"]

    assert data1["group"] == data2["group"]
    assert data1["category"] == data2["category"]
    assert data1["no"] == data2["no"]
    assert data1["anime_pattern"] == data2["anime_pattern"]
    assert abs(data1["anime_speed"] - data2["anime_speed"]) < 1e-6

    assert len(data1["colors"]) == len(data2["colors"])
    for i, (c1, c2) in enumerate(zip(data1["colors"], data2["colors"])):
        if c1 is None:
            assert c2 is None, f"Color {i} mismatch: None vs {c2}"
        else:
            assert c1 == c2, f"Color {i} mismatch: {c1} vs {c2}"

    assert len(data1["patterns"]) == len(data2["patterns"])
    for i, (p1, p2) in enumerate(zip(data1["patterns"], data2["patterns"])):
        assert p1["key"] == p2["key"], f"Pattern {i} key mismatch"
        assert p1["clamp"] == p2["clamp"], f"Pattern {i} clamp mismatch"
        assert p1["uv"] == p2["uv"], f"Pattern {i} uv mismatch"

    os.unlink(tmpfile.name)


def test_folder_data_preservation():
    """Test that folder-specific data is preserved through save/load cycle"""
    scene_data = HoneycomeSceneData.load("./data/hc_scene_items.png")

    folder_obj = None
    folder_key = None
    for key, obj in scene_data.objects.items():
        if obj["type"] == 3:
            folder_obj = obj
            folder_key = key
            break

    if folder_obj is None:
        return

    tmpfile = tempfile.NamedTemporaryFile(delete=False)
    scene_data.save(tmpfile.name)
    scene_data2 = HoneycomeSceneData.load(tmpfile.name)

    folder_obj2 = scene_data2.objects[folder_key]

    data1 = folder_obj["data"]
    data2 = folder_obj2["data"]

    assert data1["name"] == data2["name"]
    assert len(data1.get("child", [])) == len(data2.get("child", []))

    os.unlink(tmpfile.name)


# ============================================================
# Tests for hc_scene_objects.png
# ============================================================


def test_load_honeycome_scene_objects():
    """Test loading hc_scene_objects.png which contains various object types"""
    scene_data = HoneycomeSceneData.load("./data/hc_scene_objects.png")

    assert hasattr(scene_data, "version")
    assert hasattr(scene_data, "objects")
    assert len(scene_data.objects) == 8

    type_counts = {}
    for obj in scene_data.objects.values():
        t = obj["type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    assert type_counts.get(2, 0) == 2, "Expected 2 light objects"
    assert type_counts.get(3, 0) == 5, "Expected 5 folder objects"
    assert type_counts.get(4, 0) == 1, "Expected 1 route object"


def test_count_object_types_honeycome_scene_items():
    scene_data = HoneycomeSceneData.load("./data/hc_scene_items.png")
    assert scene_data.count_object_types() == {"Folder": 76, "Item": 150}


def test_count_object_types_honeycome_scene_objects():
    scene_data = HoneycomeSceneData.load("./data/hc_scene_objects.png")
    assert scene_data.count_object_types() == {
        "Folder": 8,
        "Item": 1,
        "Character": 1,
        "Light": 3,
        "Camera": 1,
        "Route": 1,
    }


def test_walk_filter_object_type_honeycome():
    scene_data = HoneycomeSceneData.load("./data/hc_scene_objects.png")
    folders = list(scene_data.walk(object_type=HoneycomeSceneData.FOLDER))
    assert len(folders) == scene_data.count_object_types()["Folder"]
    assert all(obj["type"] == HoneycomeSceneData.FOLDER for _, obj in folders)


def test_walk_filter_object_type_honeycome_with_depth():
    scene_data = HoneycomeSceneData.load("./data/hc_scene_objects.png")
    cameras = list(scene_data.walk(include_depth=True, object_type=HoneycomeSceneData.CAMERA))
    assert len(cameras) == scene_data.count_object_types()["Camera"]
    assert all(obj["type"] == HoneycomeSceneData.CAMERA for _, obj, _ in cameras)


def test_light_data_preservation():
    """Test that light-specific data is preserved through save/load cycle"""
    scene_data = HoneycomeSceneData.load("./data/hc_scene_objects.png")

    light_obj = None
    light_key = None
    for key, obj in scene_data.objects.items():
        if obj["type"] == 2:
            light_obj = obj
            light_key = key
            break

    assert light_obj is not None, "Expected at least one light object"

    tmpfile = tempfile.NamedTemporaryFile(delete=False)
    scene_data.save(tmpfile.name)
    scene_data2 = HoneycomeSceneData.load(tmpfile.name)

    light_obj2 = scene_data2.objects[light_key]

    data1 = light_obj["data"]
    data2 = light_obj2["data"]

    assert data1["no"] == data2["no"], "Light no mismatch"
    assert data1["color"] == data2["color"], "Light color mismatch"
    assert abs(data1["intensity"] - data2["intensity"]) < 1e-6, "Light intensity mismatch"
    assert abs(data1["range"] - data2["range"]) < 1e-6, "Light range mismatch"
    assert abs(data1["outsideSpotAngle"] - data2["outsideSpotAngle"]) < 1e-6, "Light outsideSpotAngle mismatch"
    assert abs(data1["insideSpotAngle"] - data2["insideSpotAngle"]) < 1e-6, "Light insideSpotAngle mismatch"
    assert data1["shadow"] == data2["shadow"], "Light shadow mismatch"

    os.unlink(tmpfile.name)


def test_route_data_preservation():
    """Test that route-specific data is preserved through save/load cycle"""
    scene_data = HoneycomeSceneData.load("./data/hc_scene_objects.png")

    route_obj = None
    route_key = None
    for key, obj in scene_data.objects.items():
        if obj["type"] == 4:
            route_obj = obj
            route_key = key
            break

    assert route_obj is not None, "Expected at least one route object"

    tmpfile = tempfile.NamedTemporaryFile(delete=False)
    scene_data.save(tmpfile.name)
    scene_data2 = HoneycomeSceneData.load(tmpfile.name)

    route_obj2 = scene_data2.objects[route_key]

    data1 = route_obj["data"]
    data2 = route_obj2["data"]

    assert data1["name"] == data2["name"], "Route name mismatch"
    assert data1["active"] == data2["active"], "Route active mismatch"
    assert data1["loop"] == data2["loop"], "Route loop mismatch"
    assert data1["visibleLine"] == data2["visibleLine"], "Route visibleLine mismatch"
    assert len(data1["route_points"]) == len(data2["route_points"]), "Route points count mismatch"

    for i, (p1, p2) in enumerate(zip(data1["route_points"], data2["route_points"])):
        for field in ["position", "rotation"]:
            if field in p1 and field in p2:
                for axis in ["x", "y", "z"]:
                    assert abs(p1[field].get(axis, 0.0) - p2[field].get(axis, 0.0)) < 1e-6, f"Route point {i} {field}.{axis} mismatch"
        assert abs(p1.get("speed", 0.0) - p2.get("speed", 0.0)) < 1e-6, f"Route point {i} speed mismatch"

    os.unlink(tmpfile.name)


def _find_nested_object_by_type(folder_data, target_type):
    """Recursively find an object of target_type in folder children"""
    for child in folder_data.get("child", []):
        if child["type"] == target_type:
            return child
        if child["type"] == 3:
            result = _find_nested_object_by_type(child["data"], target_type)
            if result:
                return result
    return None


def test_nested_char_data_preservation():
    """Test that nested character data is preserved through save/load cycle"""
    scene_data = HoneycomeSceneData.load("./data/hc_scene_objects.png")

    char_obj = None
    for obj in scene_data.objects.values():
        if obj["type"] == 3:
            char_obj = _find_nested_object_by_type(obj["data"], 0)
            if char_obj:
                break

    assert char_obj is not None, "Expected at least one nested character object"

    tmpfile = tempfile.NamedTemporaryFile(delete=False)
    scene_data.save(tmpfile.name)
    scene_data2 = HoneycomeSceneData.load(tmpfile.name)

    char_obj2 = None
    for obj in scene_data2.objects.values():
        if obj["type"] == 3:
            char_obj2 = _find_nested_object_by_type(obj["data"], 0)
            if char_obj2:
                break

    assert char_obj2 is not None, "Expected nested character object after reload"

    data1 = char_obj["data"]
    data2 = char_obj2["data"]

    assert data1["dicKey"] == data2["dicKey"], "Char dicKey mismatch"
    assert data1["visible"] == data2["visible"], "Char visible mismatch"
    assert "character" in data1, "Expected character in character object"
    assert "character" in data2, "Expected character in reloaded character object"

    os.unlink(tmpfile.name)


def test_nested_camera_data_preservation():
    """Test that nested camera data is preserved through save/load cycle"""
    scene_data = HoneycomeSceneData.load("./data/hc_scene_objects.png")

    camera_obj = None
    for obj in scene_data.objects.values():
        if obj["type"] == 3:
            camera_obj = _find_nested_object_by_type(obj["data"], 5)
            if camera_obj:
                break

    assert camera_obj is not None, "Expected at least one nested camera object"

    tmpfile = tempfile.NamedTemporaryFile(delete=False)
    scene_data.save(tmpfile.name)
    scene_data2 = HoneycomeSceneData.load(tmpfile.name)

    camera_obj2 = None
    for obj in scene_data2.objects.values():
        if obj["type"] == 3:
            camera_obj2 = _find_nested_object_by_type(obj["data"], 5)
            if camera_obj2:
                break

    assert camera_obj2 is not None, "Expected nested camera object after reload"

    data1 = camera_obj["data"]
    data2 = camera_obj2["data"]

    assert data1["dicKey"] == data2["dicKey"], "Camera dicKey mismatch"
    assert data1["active"] == data2["active"], "Camera active mismatch"

    os.unlink(tmpfile.name)


def test_nested_item_data_preservation():
    """Test that nested item data is preserved through save/load cycle"""
    scene_data = HoneycomeSceneData.load("./data/hc_scene_objects.png")

    item_obj = None
    for obj in scene_data.objects.values():
        if obj["type"] == 3:
            item_obj = _find_nested_object_by_type(obj["data"], 1)
            if item_obj:
                break

    assert item_obj is not None, "Expected at least one nested item object"

    tmpfile = tempfile.NamedTemporaryFile(delete=False)
    scene_data.save(tmpfile.name)
    scene_data2 = HoneycomeSceneData.load(tmpfile.name)

    item_obj2 = None
    for obj in scene_data2.objects.values():
        if obj["type"] == 3:
            item_obj2 = _find_nested_object_by_type(obj["data"], 1)
            if item_obj2:
                break

    assert item_obj2 is not None, "Expected nested item object after reload"

    data1 = item_obj["data"]
    data2 = item_obj2["data"]

    assert data1["group"] == data2["group"], "Item group mismatch"
    assert data1["category"] == data2["category"], "Item category mismatch"
    assert data1["no"] == data2["no"], "Item no mismatch"

    os.unlink(tmpfile.name)
