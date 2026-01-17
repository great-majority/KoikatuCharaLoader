import json
import struct
from typing import Any, BinaryIO, Dict

from kkloader.funcs import load_length, load_string, write_string
from kkloader.KoikatuCharaData import KoikatuCharaData


class KoikatuSceneObjectLoader:
    """
    Class for loading Koikatu scene object data.
    This is a Python implementation of the Studio.ObjectInfo.Load functions in C#.
    """

    # ============================================================
    # 1. DISPATCH TABLES & CONFIGURATION
    # ============================================================
    """
    Object type dispatching system.

    Maps object type IDs to their respective load/save handler methods.
    Supported object types:
      0: Character (OICharInfo)
      1: Item (OIItemInfo)
      2: Light (OILightInfo)
      3: Folder (OIFolderInfo)
      4: Route (OIRouteInfo)
      5: Camera (OICameraInfo)
      7: Text (OITextInfo)
    """

    # Object type dispatch tables
    _LOAD_DISPATCH = {
        0: "load_char_info",
        1: "load_item_info",
        2: "load_light_info",
        3: "load_folder_info",
        4: "load_route_info",
        5: "load_camera_info",
        7: "load_text_info",
    }

    _SAVE_DISPATCH = {
        0: "save_char_info",
        1: "save_item_info",
        2: "save_light_info",
        3: "save_folder_info",
        4: "save_route_info",
        5: "save_camera_info",
        7: "save_text_info",
    }

    @staticmethod
    def _dispatch_load(data_stream: BinaryIO, obj_type: int, obj_info: Dict[str, Any], version: str = None) -> None:
        """Dispatch to appropriate load method based on object type"""
        method_name = KoikatuSceneObjectLoader._LOAD_DISPATCH.get(obj_type)
        if method_name is None:
            print(f"Warning: Unknown object type {obj_type}")
            return
        method = getattr(KoikatuSceneObjectLoader, method_name)
        method(data_stream, obj_info, version)

    @staticmethod
    def _dispatch_save(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """Dispatch to appropriate save method based on object type"""
        obj_type = obj_info.get("type", -1)
        method_name = KoikatuSceneObjectLoader._SAVE_DISPATCH.get(obj_type)
        if method_name is None:
            raise ValueError(f"Unknown object type: {obj_type}")
        method = getattr(KoikatuSceneObjectLoader, method_name)
        method(data_stream, obj_info, version)

    # ============================================================
    # 2. PRIMITIVE TYPE HELPERS
    # ============================================================
    """
    Low-level data structure helpers for binary serialization.

    These methods handle the most basic data types used throughout
    the scene file format: Vector3, Color (RGBA/JSON), and boolean arrays.
    All methods are private as they're only used internally by higher-level loaders/savers.
    """

    @staticmethod
    def _load_vector3(data_stream: BinaryIO) -> Dict[str, float]:
        """Load a Vector3 (x, y, z) from the data stream"""
        return {"x": struct.unpack("f", data_stream.read(4))[0], "y": struct.unpack("f", data_stream.read(4))[0], "z": struct.unpack("f", data_stream.read(4))[0]}

    @staticmethod
    def _save_vector3(data_stream: BinaryIO, vector3: Dict[str, float], default: float = 0.0) -> None:
        """Save a Vector3 (x, y, z) to the data stream"""
        data_stream.write(struct.pack("f", vector3.get("x", default)))
        data_stream.write(struct.pack("f", vector3.get("y", default)))
        data_stream.write(struct.pack("f", vector3.get("z", default)))

    @staticmethod
    def _load_color_rgba(data_stream: BinaryIO) -> Dict[str, float]:
        """Load a Color (r, g, b, a) from the data stream"""
        return {"r": struct.unpack("f", data_stream.read(4))[0], "g": struct.unpack("f", data_stream.read(4))[0], "b": struct.unpack("f", data_stream.read(4))[0], "a": struct.unpack("f", data_stream.read(4))[0]}

    @staticmethod
    def _save_color_rgba(data_stream: BinaryIO, color: Dict[str, float]) -> None:
        """Save Color (r, g, b, a) as 4 floats"""
        data_stream.write(struct.pack("f", color.get("r", 1.0)))
        data_stream.write(struct.pack("f", color.get("g", 1.0)))
        data_stream.write(struct.pack("f", color.get("b", 1.0)))
        data_stream.write(struct.pack("f", color.get("a", 1.0)))

    @staticmethod
    def parse_color_json(json_str: str) -> Dict[str, float]:
        """Parse color from JSON string"""
        # JSONとして解析
        color_data = json.loads(json_str)
        return {"r": color_data.get("r", 0), "g": color_data.get("g", 0), "b": color_data.get("b", 0), "a": color_data.get("a", 1.0)}

    @staticmethod
    def _save_color_json(data_stream: BinaryIO, color: Dict[str, float]) -> None:
        """Save Color as JSON string with length prefix"""
        color_bytes = json.dumps(color, separators=(",", ":")).encode("utf-8")
        write_string(data_stream, color_bytes)

    @staticmethod
    def _load_bool_array(data_stream: BinaryIO, count: int) -> list:
        """Load an array of boolean values from the data stream"""
        return [bool(struct.unpack("b", data_stream.read(1))[0]) for _ in range(count)]

    # ============================================================
    # 3. BASE OBJECT INFO HELPERS
    # ============================================================
    """
    Base object information handlers.

    These methods handle the common data fields that all scene objects share:
    dicKey, position, rotation, scale, and other basic object properties.
    Includes specialized handling for light object bases.
    """

    @staticmethod
    def _load_object_info_base(data_stream: BinaryIO) -> Dict[str, Any]:
        """Load ObjectInfo base data (dicKey, position, rotation, scale, treeState, visible)"""
        return {
            "dicKey": struct.unpack("i", data_stream.read(4))[0],
            "position": KoikatuSceneObjectLoader._load_vector3(data_stream),
            "rotation": KoikatuSceneObjectLoader._load_vector3(data_stream),
            "scale": KoikatuSceneObjectLoader._load_vector3(data_stream),
            "treeState": struct.unpack("i", data_stream.read(4))[0],
            "visible": bool(struct.unpack("b", data_stream.read(1))[0]),
        }

    @staticmethod
    def _save_object_info_base(data_stream: BinaryIO, data: Dict[str, Any]) -> None:
        """Save ObjectInfo base data (ObjectInfo.Save)"""
        # Save dicKey, changeAmount (position, rotation, scale), treeState, visible

        # Write dicKey (int)
        data_stream.write(struct.pack("i", data.get("dicKey", 0)))

        # Write position (Vector3)
        pos = data.get("position", {"x": 0.0, "y": 0.0, "z": 0.0})
        KoikatuSceneObjectLoader._save_vector3(data_stream, pos, default=0.0)

        # Write rotation (Vector3)
        rot = data.get("rotation", {"x": 0.0, "y": 0.0, "z": 0.0})
        KoikatuSceneObjectLoader._save_vector3(data_stream, rot, default=0.0)

        # Write scale (Vector3)
        scale = data.get("scale", {"x": 1.0, "y": 1.0, "z": 1.0})
        KoikatuSceneObjectLoader._save_vector3(data_stream, scale, default=1.0)

        # Write treeState
        data_stream.write(struct.pack("i", data.get("treeState", 0)))

        # Write visible
        data_stream.write(struct.pack("b", int(data.get("visible", True))))

    @staticmethod
    def _load_light_info_base(data_stream: BinaryIO) -> Dict[str, Any]:
        """Load base light info (color, intensity, rot, shadow)"""
        color_json = load_string(data_stream).decode("utf-8")
        return {
            "color": KoikatuSceneObjectLoader.parse_color_json(color_json),
            "intensity": struct.unpack("f", data_stream.read(4))[0],
            "rot": [struct.unpack("f", data_stream.read(4))[0], struct.unpack("f", data_stream.read(4))[0]],
            "shadow": bool(struct.unpack("b", data_stream.read(1))[0]),
        }

    @staticmethod
    def _save_light_info_base(data_stream: BinaryIO, light_data: Dict[str, Any]) -> None:
        """Save base light info (color, intensity, rot, shadow)"""
        color_bytes = json.dumps(light_data["color"], separators=(",", ":")).encode("utf-8")
        write_string(data_stream, color_bytes)
        data_stream.write(struct.pack("f", light_data["intensity"]))
        data_stream.write(struct.pack("f", light_data["rot"][0]))
        data_stream.write(struct.pack("f", light_data["rot"][1]))
        data_stream.write(struct.pack("b", int(light_data["shadow"])))

    # ============================================================
    # 4. COMPONENT DATA HELPERS
    # ============================================================
    """
    Component-level data structure handlers.

    These methods handle complex sub-components that are used by multiple object types:
    - BoneInfo: FK/IK bone data for characters and items
    - PatternInfo: Texture pattern data for items
    - RoutePointInfo: Waypoint data for route objects
    All methods follow the Load/Save pattern matching their C# counterparts.
    """

    @staticmethod
    def load_bone_info(data_stream: BinaryIO) -> Dict[str, Any]:
        """
        Load bone info data
        Based on OIBoneInfo.Save/Load in C#

        OIBoneInfo.Save writes: dicKey + changeAmount (3 Vector3)
        OIBoneInfo.Load calls: base.Load(_other: false) which reads dicKey + changeAmount only
        """
        bone_data = {}

        # Read dicKey (int)
        bone_data["dicKey"] = struct.unpack("i", data_stream.read(4))[0]

        # Read ChangeAmount (ChangeAmount.Load/Save in C#)
        # ChangeAmount contains 3 Vector3: position, rotation, scale
        bone_data["changeAmount"] = {"position": KoikatuSceneObjectLoader._load_vector3(data_stream), "rotation": KoikatuSceneObjectLoader._load_vector3(data_stream), "scale": KoikatuSceneObjectLoader._load_vector3(data_stream)}

        return bone_data

    @staticmethod
    def save_bone_info(data_stream: BinaryIO, bone_data: Dict[str, Any]) -> None:
        """Save bone info data"""
        # Based on OIBoneInfo.Save in C#
        # Write dicKey
        data_stream.write(struct.pack("i", bone_data.get("dicKey", 0)))

        # Write changeAmount (position, rotation, scale)
        change_amount = bone_data.get("changeAmount", {})
        KoikatuSceneObjectLoader._save_vector3(data_stream, change_amount.get("position", {"x": 0.0, "y": 0.0, "z": 0.0}))
        KoikatuSceneObjectLoader._save_vector3(data_stream, change_amount.get("rotation", {"x": 0.0, "y": 0.0, "z": 0.0}))
        KoikatuSceneObjectLoader._save_vector3(data_stream, change_amount.get("scale", {"x": 1.0, "y": 1.0, "z": 1.0}))

    @staticmethod
    def load_pattern_info(data_stream: BinaryIO) -> Dict[str, Any]:
        """Load pattern info data"""
        # Based on PatternInfo.Load in C#
        pattern_data = {}

        # Read key
        pattern_data["key"] = struct.unpack("i", data_stream.read(4))[0]

        # Read filePath using load_string
        file_path_bytes = load_string(data_stream)
        pattern_data["file_path"] = file_path_bytes.decode("utf-8")

        # Read clamp
        pattern_data["clamp"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read uv (Vector4)
        uv_json = load_string(data_stream).decode("utf-8")
        pattern_data["uv"] = json.loads(uv_json)

        # Read rot
        pattern_data["rot"] = struct.unpack("f", data_stream.read(4))[0]

        return pattern_data

    @staticmethod
    def save_pattern_info(data_stream: BinaryIO, pattern_data: Dict[str, Any]) -> None:
        """Save pattern info data"""
        # Based on PatternInfo.Save in C#

        # Write key
        data_stream.write(struct.pack("i", pattern_data["key"]))

        # Write filePath
        write_string(data_stream, pattern_data["file_path"].encode("utf-8"))

        # Write clamp
        data_stream.write(struct.pack("b", int(pattern_data["clamp"])))

        # Write uv (Vector4)
        write_string(data_stream, json.dumps(pattern_data["uv"], separators=(",", ":")).encode("utf-8"))

        # Write rot
        data_stream.write(struct.pack("f", pattern_data["rot"]))

    @staticmethod
    def _load_route_point_info(data_stream: BinaryIO, version: str = None) -> Dict[str, Any]:
        """
        Load OIRoutePointInfo data with version-specific handling
        Based on OIRoutePointInfo.Load in C# (lines 50-75)
        """
        route_point = {}

        # Read dicKey
        route_point["dicKey"] = struct.unpack("i", data_stream.read(4))[0]

        # Read ChangeAmount (3 Vector3)
        route_point["changeAmount"] = {"position": KoikatuSceneObjectLoader._load_vector3(data_stream), "rotation": KoikatuSceneObjectLoader._load_vector3(data_stream), "scale": KoikatuSceneObjectLoader._load_vector3(data_stream)}

        # Read speed
        route_point["speed"] = struct.unpack("f", data_stream.read(4))[0]

        # Read easeType
        route_point["easeType"] = struct.unpack("i", data_stream.read(4))[0]

        # Version 1.0.3 only: read and discard a boolean
        if KoikatuSceneObjectLoader._compare_versions(version, "1.0.3") == 0:
            data_stream.read(1)  # Discard boolean

        # Version >= 1.0.4.1: connection
        if KoikatuSceneObjectLoader._compare_versions(version, "1.0.4.1") >= 0:
            route_point["connection"] = struct.unpack("i", data_stream.read(4))[0]

        # Version >= 1.0.4.1: aidInfo
        if KoikatuSceneObjectLoader._compare_versions(version, "1.0.4.1") >= 0:
            route_point["aidInfo"] = KoikatuSceneObjectLoader._load_route_point_aid_info(data_stream)

        # Version >= 1.0.4.2: link
        if KoikatuSceneObjectLoader._compare_versions(version, "1.0.4.2") >= 0:
            route_point["link"] = bool(struct.unpack("b", data_stream.read(1))[0])

        return route_point

    @staticmethod
    def _save_route_point_info(data_stream: BinaryIO, route_point: Dict[str, Any]) -> None:
        """
        Save OIRoutePointInfo data
        Based on OIRoutePointInfo.Save in C#
        """
        # Write dicKey
        data_stream.write(struct.pack("i", route_point.get("dicKey", 0)))

        # Write ChangeAmount (3 Vector3: position, rotation, scale)
        change_amount = route_point.get("changeAmount", {})
        KoikatuSceneObjectLoader._save_vector3(data_stream, change_amount.get("position", {"x": 0.0, "y": 0.0, "z": 0.0}))
        KoikatuSceneObjectLoader._save_vector3(data_stream, change_amount.get("rotation", {"x": 0.0, "y": 0.0, "z": 0.0}))
        KoikatuSceneObjectLoader._save_vector3(data_stream, change_amount.get("scale", {"x": 1.0, "y": 1.0, "z": 1.0}))

        # Write speed
        data_stream.write(struct.pack("f", route_point.get("speed", 2.0)))

        # Write easeType
        data_stream.write(struct.pack("i", route_point.get("easeType", 0)))

        # Write connection
        data_stream.write(struct.pack("i", route_point.get("connection", 0)))

        # Write aidInfo
        aid_info = route_point.get("aidInfo", {})
        KoikatuSceneObjectLoader._save_route_point_aid_info(data_stream, aid_info)

        # Write link
        data_stream.write(struct.pack("b", int(route_point.get("link", False))))

    @staticmethod
    def _load_route_point_aid_info(data_stream: BinaryIO) -> Dict[str, Any]:
        """
        Load OIRoutePointAidInfo data
        Based on OIRoutePointAidInfo.Load in C#
        """
        aid_info = {}

        # Read dicKey
        aid_info["dicKey"] = struct.unpack("i", data_stream.read(4))[0]

        # Read ChangeAmount (3 Vector3)
        aid_info["changeAmount"] = {"position": KoikatuSceneObjectLoader._load_vector3(data_stream), "rotation": KoikatuSceneObjectLoader._load_vector3(data_stream), "scale": KoikatuSceneObjectLoader._load_vector3(data_stream)}

        # Read isInit
        aid_info["isInit"] = bool(struct.unpack("b", data_stream.read(1))[0])

        return aid_info

    @staticmethod
    def _save_route_point_aid_info(data_stream: BinaryIO, aid_info: Dict[str, Any]) -> None:
        """
        Save OIRoutePointAidInfo data
        Based on OIRoutePointAidInfo.Save in C#
        """
        # Write dicKey
        data_stream.write(struct.pack("i", aid_info.get("dicKey", 0)))

        # Write ChangeAmount (3 Vector3: position, rotation, scale)
        change_amount = aid_info.get("changeAmount", {})
        KoikatuSceneObjectLoader._save_vector3(data_stream, change_amount.get("position", {"x": 0.0, "y": 0.0, "z": 0.0}))
        KoikatuSceneObjectLoader._save_vector3(data_stream, change_amount.get("rotation", {"x": 0.0, "y": 0.0, "z": 0.0}))
        KoikatuSceneObjectLoader._save_vector3(data_stream, change_amount.get("scale", {"x": 1.0, "y": 1.0, "z": 1.0}))

        # Write isInit
        data_stream.write(struct.pack("b", int(aid_info.get("isInit", False))))

    # ============================================================
    # 5. OBJECT TYPE LOADERS
    # ============================================================
    """
    Object type-specific load methods.

    Each method handles loading a specific type of scene object:
    - load_char_info: Characters (OICharInfo)
    - load_item_info: Scene items (OIItemInfo)
    - load_light_info: Light sources (OILightInfo)
    - load_folder_info: Object folders (OIFolderInfo)
    - load_route_info: Movement routes (OIRouteInfo)
    - load_camera_info: Camera objects (OICameraInfo)
    - load_text_info: Text objects (OITextInfo)

    All methods populate the obj_info dictionary with loaded data.
    """

    @staticmethod
    def load_char_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """Load character info data"""
        # Based on OICharInfo.Load in C#
        # Load ObjectInfo base data (dicKey, position, rotation, scale, treeState, visible)
        data = KoikatuSceneObjectLoader._load_object_info_base(data_stream)

        # Read sex
        data["sex"] = struct.unpack("i", data_stream.read(4))[0]

        # Load character file data using KoikatuCharaData
        # This corresponds to ChaFileControl.LoadCharaFile in C#
        # C# calls with noLoadPng: true, so contains_png=False
        try:
            chara_data = KoikatuCharaData.load(data_stream, contains_png=False)
            data["character"] = chara_data
        except Exception as e:
            stream_pos_error = data_stream.tell()
            print(f"Warning: Error reading character file data at position {stream_pos_error}: {type(e).__name__}: {str(e)}")
            import traceback

            traceback.print_exc()

            # CRITICAL: If character loading fails, we cannot continue
            # because we don't know where the stream position should be
            raise RuntimeError(f"Failed to load character data: {str(e)}") from e

        # Read bones count
        bones_count = struct.unpack("i", data_stream.read(4))[0]
        data["bones"] = {}

        # Read bones data
        for _ in range(bones_count):
            bone_key = struct.unpack("i", data_stream.read(4))[0]
            bone_data = KoikatuSceneObjectLoader.load_bone_info(data_stream)
            data["bones"][bone_key] = bone_data

        # Read IK targets count
        ik_count = struct.unpack("i", data_stream.read(4))[0]
        data["ik_targets"] = {}

        # Read IK targets data (OIIKTargetInfo extends OIBoneInfo)
        for _ in range(ik_count):
            ik_key = struct.unpack("i", data_stream.read(4))[0]
            ik_data = KoikatuSceneObjectLoader.load_bone_info(data_stream)
            data["ik_targets"][ik_key] = ik_data

        # Read child objects count (Dictionary<int, List<ObjectInfo>>)
        child_count = struct.unpack("i", data_stream.read(4))[0]
        data["child"] = {}

        # Read child objects data for each key
        for child_idx in range(child_count):
            child_key = struct.unpack("i", data_stream.read(4))[0]
            # Load child objects recursively for this key
            data["child"][child_key] = KoikatuSceneObjectLoader.load_child_objects(data_stream, version)

        # Read kinematic mode
        data["kinematic_mode"] = struct.unpack("i", data_stream.read(4))[0]

        # Read anime info
        data["anime_info"] = {"group": struct.unpack("i", data_stream.read(4))[0], "category": struct.unpack("i", data_stream.read(4))[0], "no": struct.unpack("i", data_stream.read(4))[0]}

        # Read hand patterns
        data["hand_patterns"] = [struct.unpack("i", data_stream.read(4))[0], struct.unpack("i", data_stream.read(4))[0]]

        # Read nipple
        data["nipple"] = struct.unpack("f", data_stream.read(4))[0]

        # Read siru
        data["siru"] = data_stream.read(5)

        # Read mouth open
        data["mouth_open"] = struct.unpack("f", data_stream.read(4))[0]

        # Read lip sync
        data["lip_sync"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read look at target info (LookAtTargetInfo.Load)
        # base.Load with _other=false: only dicKey and changeAmount, no treeState/visible
        data["lookAtTarget"] = {
            "dicKey": struct.unpack("i", data_stream.read(4))[0],
            "position": KoikatuSceneObjectLoader._load_vector3(data_stream),
            "rotation": KoikatuSceneObjectLoader._load_vector3(data_stream),
            "scale": KoikatuSceneObjectLoader._load_vector3(data_stream),
        }

        # Read enable IK
        data["enable_ik"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read active IK
        data["active_ik"] = KoikatuSceneObjectLoader._load_bool_array(data_stream, 5)

        # Read enable FK
        data["enable_fk"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read active FK
        data["active_fk"] = KoikatuSceneObjectLoader._load_bool_array(data_stream, 7)

        # Read expression (4 for version < 0.0.9, 8 for version >= 0.0.9)
        expression_count = 8 if KoikatuSceneObjectLoader._compare_versions(version, "0.0.9") >= 0 else 4
        data["expression"] = KoikatuSceneObjectLoader._load_bool_array(data_stream, expression_count)

        # Read anime speed
        data["anime_speed"] = struct.unpack("f", data_stream.read(4))[0]

        # Read anime pattern
        data["anime_pattern"] = struct.unpack("f", data_stream.read(4))[0]

        # Read anime option visible
        data["anime_option_visible"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read is anime force loop
        data["is_anime_force_loop"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read voice ctrl (VoiceCtrl.Load)
        voice_list_count = struct.unpack("i", data_stream.read(4))[0]
        data["voiceCtrl"] = {"list": [], "repeat": None}
        for _ in range(voice_list_count):
            voice_info = {"group": struct.unpack("i", data_stream.read(4))[0], "category": struct.unpack("i", data_stream.read(4))[0], "no": struct.unpack("i", data_stream.read(4))[0]}
            data["voiceCtrl"]["list"].append(voice_info)
        data["voiceCtrl"]["repeat"] = struct.unpack("i", data_stream.read(4))[0]

        # Read visible son
        data["visible_son"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read son length
        data["son_length"] = struct.unpack("f", data_stream.read(4))[0]

        # Read visible simple
        data["visible_simple"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read simple color
        simple_color_json = load_length(data_stream, "b").decode("utf-8")
        try:
            data["simple_color"] = KoikatuSceneObjectLoader.parse_color_json(simple_color_json)
        except ValueError as e:
            print(f"Warning: Error parsing simple color JSON: {str(e)}")
            data["simple_color"] = {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}

        # Read anime option param
        data["anime_option_param"] = [struct.unpack("f", data_stream.read(4))[0], struct.unpack("f", data_stream.read(4))[0]]

        # Read neck byte data
        neck_data_length = struct.unpack("i", data_stream.read(4))[0]
        data["neck_byte_data"] = data_stream.read(neck_data_length)

        # Read eyes byte data
        eyes_data_length = struct.unpack("i", data_stream.read(4))[0]
        data["eyes_byte_data"] = data_stream.read(eyes_data_length)

        # Read anime normalized time
        data["anime_normalized_time"] = struct.unpack("f", data_stream.read(4))[0]

        # Read dic access group
        dic_access_group_count = struct.unpack("i", data_stream.read(4))[0]
        data["dic_access_group"] = {}
        for _ in range(dic_access_group_count):
            key = struct.unpack("i", data_stream.read(4))[0]
            value = struct.unpack("i", data_stream.read(4))[0]
            data["dic_access_group"][key] = value

        # Read dic access no
        dic_access_no_count = struct.unpack("i", data_stream.read(4))[0]
        data["dic_access_no"] = {}
        for _ in range(dic_access_no_count):
            key = struct.unpack("i", data_stream.read(4))[0]
            value = struct.unpack("i", data_stream.read(4))[0]
            data["dic_access_no"][key] = value

        obj_info["data"] = data

    @staticmethod
    def load_item_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """Load item info data"""
        # Based on OIItemInfo.Load in C#
        # Load ObjectInfo base data (dicKey, position, rotation, scale, treeState, visible)
        data = KoikatuSceneObjectLoader._load_object_info_base(data_stream)

        # Read group, category, no
        data["group"] = struct.unpack("i", data_stream.read(4))[0]
        data["category"] = struct.unpack("i", data_stream.read(4))[0]
        data["no"] = struct.unpack("i", data_stream.read(4))[0]

        # Read anime pattern (version >= 1.1.1.0)
        if KoikatuSceneObjectLoader._compare_versions(version, "1.1.1.0") >= 0:
            data["anime_pattern"] = struct.unpack("i", data_stream.read(4))[0]
        else:
            data["anime_pattern"] = 0  # Default value for older versions

        # Read anime speed
        data["anime_speed"] = struct.unpack("f", data_stream.read(4))[0]

        # Read colors (version dependent)
        data["colors"] = []
        if KoikatuSceneObjectLoader._compare_versions(version, "0.0.3") >= 0:
            # Version >= 0.0.3: read 8 colors
            for _ in range(8):
                color_bytes = load_string(data_stream)
                if len(color_bytes) > 0:
                    data["colors"].append(json.loads(color_bytes.decode("utf-8")))
                else:
                    data["colors"].append(None)
        else:
            # Version < 0.0.3: read 7 colors, pad to 8 with white
            for _ in range(7):
                color_bytes = load_string(data_stream)
                if len(color_bytes) > 0:
                    data["colors"].append(json.loads(color_bytes.decode("utf-8")))
                else:
                    data["colors"].append(None)
            # Add 8th color as default white
            data["colors"].append({"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0})

        # Read patterns
        data["patterns"] = []
        for _ in range(3):
            pattern_data = KoikatuSceneObjectLoader.load_pattern_info(data_stream)
            data["patterns"].append(pattern_data)

        # Read alpha
        data["alpha"] = struct.unpack("f", data_stream.read(4))[0]

        # Read line color and width (version >= 0.0.4)
        if KoikatuSceneObjectLoader._compare_versions(version, "0.0.4") >= 0:
            line_color_json = load_string(data_stream).decode("utf-8")
            data["line_color"] = json.loads(line_color_json)
            data["line_width"] = struct.unpack("f", data_stream.read(4))[0]
        else:
            # Default values for older versions (from C# constructor)
            data["line_color"] = {"r": 128.0 / 255.0, "g": 128.0 / 255.0, "b": 128.0 / 255.0, "a": 1.0}
            data["line_width"] = 1.0

        # Read emission color, power, and light cancel (version >= 0.0.7)
        if KoikatuSceneObjectLoader._compare_versions(version, "0.0.7") >= 0:
            emission_color_json = load_string(data_stream).decode("utf-8")
            data["emission_color"] = json.loads(emission_color_json)
            data["emission_power"] = struct.unpack("f", data_stream.read(4))[0]
            data["light_cancel"] = struct.unpack("f", data_stream.read(4))[0]
        else:
            # Default values for older versions (from C# constructor)
            data["emission_color"] = {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}
            data["emission_power"] = 0.0
            data["light_cancel"] = 0.0

        # Read panel (version >= 0.0.6)
        if KoikatuSceneObjectLoader._compare_versions(version, "0.0.6") >= 0:
            data["panel"] = KoikatuSceneObjectLoader.load_pattern_info(data_stream)
        else:
            # Default empty PatternInfo (from C# constructor)
            data["panel"] = {"key": 0, "file_path": "", "clamp": True, "uv": {"x": 0.0, "y": 0.0, "z": 1.0, "w": 1.0}, "rot": 0.0}

        # Read enable FK
        data["enable_fk"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read bones count
        bones_count = struct.unpack("i", data_stream.read(4))[0]
        data["bones"] = {}

        # Read bones data (Dictionary<string, OIBoneInfo>)
        for _ in range(bones_count):
            # C# BinaryReader.ReadString() uses 7-bit encoded length
            bone_key = load_string(data_stream).decode("utf-8")
            bone_data = KoikatuSceneObjectLoader.load_bone_info(data_stream)
            data["bones"][bone_key] = bone_data

        # Read enable dynamic bone (version >= 1.0.1)
        if KoikatuSceneObjectLoader._compare_versions(version, "1.0.1") >= 0:
            data["enable_dynamic_bone"] = bool(struct.unpack("b", data_stream.read(1))[0])
        else:
            # Default value for older versions (from C# field declaration)
            data["enable_dynamic_bone"] = True

        # Read anime normalized time
        data["anime_normalized_time"] = struct.unpack("f", data_stream.read(4))[0]

        # Load child objects recursively (List<ObjectInfo>)
        data["child"] = KoikatuSceneObjectLoader.load_child_objects(data_stream, version)

        obj_info["data"] = data

    @staticmethod
    def load_light_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """
        Load light info data
        Based on OILightInfo.Load in C#
        """
        # Load ObjectInfo base data (dicKey, position, rotation, scale, treeState, visible)
        data = KoikatuSceneObjectLoader._load_object_info_base(data_stream)

        # Read light-specific data
        data["no"] = struct.unpack("i", data_stream.read(4))[0]

        # Read color (Utility.LoadColor - 4 floats: r, g, b, a)
        data["color"] = KoikatuSceneObjectLoader._load_color_rgba(data_stream)

        data["intensity"] = struct.unpack("f", data_stream.read(4))[0]
        data["range"] = struct.unpack("f", data_stream.read(4))[0]
        data["spotAngle"] = struct.unpack("f", data_stream.read(4))[0]
        data["shadow"] = bool(struct.unpack("b", data_stream.read(1))[0])
        data["enable"] = bool(struct.unpack("b", data_stream.read(1))[0])
        data["drawTarget"] = bool(struct.unpack("b", data_stream.read(1))[0])

        obj_info["data"] = data

    @staticmethod
    def load_folder_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """
        Load folder info data
        Based on OIFolderInfo.Load in C#
        """
        # Load ObjectInfo base data (dicKey, position, rotation, scale, treeState, visible)
        data = KoikatuSceneObjectLoader._load_object_info_base(data_stream)

        # Read folder name
        name_bytes = load_string(data_stream)
        data["name"] = name_bytes.decode("utf-8")

        # Load child objects recursively
        data["child"] = KoikatuSceneObjectLoader.load_child_objects(data_stream, version)

        obj_info["data"] = data

    @staticmethod
    def load_route_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """
        Load route info data with full version-specific handling
        Based on OIRouteInfo.Load in C# (lines 65-91)
        """
        # Load ObjectInfo base data (dicKey, position, rotation, scale, treeState, visible)
        data = KoikatuSceneObjectLoader._load_object_info_base(data_stream)

        # Read route name
        name_bytes = load_string(data_stream)
        data["name"] = name_bytes.decode("utf-8")

        # Load child objects recursively
        data["child"] = KoikatuSceneObjectLoader.load_child_objects(data_stream, version)

        # Read route points list
        route_points_count = struct.unpack("i", data_stream.read(4))[0]
        data["route_points"] = []
        for _ in range(route_points_count):
            route_point = KoikatuSceneObjectLoader._load_route_point_info(data_stream, version)
            data["route_points"].append(route_point)

        # Version >= 1.0.3: active, loop, visibleLine
        if KoikatuSceneObjectLoader._compare_versions(version, "1.0.3") >= 0:
            data["active"] = bool(struct.unpack("b", data_stream.read(1))[0])
            data["loop"] = bool(struct.unpack("b", data_stream.read(1))[0])
            data["visibleLine"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Version >= 1.0.4: orient
        if KoikatuSceneObjectLoader._compare_versions(version, "1.0.4") >= 0:
            data["orient"] = struct.unpack("i", data_stream.read(4))[0]

        # Version >= 1.0.4.1: color
        if KoikatuSceneObjectLoader._compare_versions(version, "1.0.4.1") >= 0:
            color_json = load_string(data_stream).decode("utf-8")
            data["color"] = json.loads(color_json)

        obj_info["data"] = data

    @staticmethod
    def load_camera_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """
        Load camera info data
        Based on OICameraInfo.Load in C#
        """
        # Load ObjectInfo base data (dicKey, position, rotation, scale, treeState, visible)
        data = KoikatuSceneObjectLoader._load_object_info_base(data_stream)

        # Read camera-specific data
        name_bytes = load_string(data_stream)
        data["name"] = name_bytes.decode("utf-8")
        data["active"] = bool(struct.unpack("b", data_stream.read(1))[0])

        obj_info["data"] = data

    @staticmethod
    def load_text_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """
        Load text info data
        Based on OITextInfo.Load in C#
        """
        # Load ObjectInfo base data (dicKey, position, rotation, scale, treeState, visible)
        data = KoikatuSceneObjectLoader._load_object_info_base(data_stream)

        # Read text-specific data
        data["id"] = struct.unpack("i", data_stream.read(4))[0]

        # Read colors
        color_json = load_string(data_stream).decode("utf-8")
        data["color"] = json.loads(color_json)

        outline_color_json = load_string(data_stream).decode("utf-8")
        data["outlineColor"] = json.loads(outline_color_json)

        data["outlineSize"] = struct.unpack("f", data_stream.read(4))[0]

        # Read textInfos array (MessagePack serialized)
        text_infos_length = struct.unpack("i", data_stream.read(4))[0]
        text_infos_bytes = data_stream.read(text_infos_length)

        # Store raw MessagePack bytes for now
        # Full deserialization would require msgpack library
        data["textInfos_raw"] = text_infos_bytes
        # NOTE: To fully deserialize, use: import msgpack; msgpack.unpackb(text_infos_bytes)

        obj_info["data"] = data

    # ============================================================
    # 6. OBJECT TYPE SAVERS
    # ============================================================
    """
    Object type-specific save methods.

    Each method handles saving a specific type of scene object:
    - save_char_info: Characters (OICharInfo)
    - save_item_info: Scene items (OIItemInfo)
    - save_light_info: Light sources (OILightInfo)
    - save_folder_info: Object folders (OIFolderInfo)
    - save_route_info: Movement routes (OIRouteInfo)
    - save_camera_info: Camera objects (OICameraInfo)
    - save_text_info: Text objects (OITextInfo)

    All methods write data from the obj_info dictionary to binary format.
    """

    @staticmethod
    def save_char_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """Save character info data"""
        # Based on OICharInfo.Save in C#
        data = obj_info["data"]

        # Save ObjectInfo base data
        KoikatuSceneObjectLoader._save_object_info_base(data_stream, data)

        # Write sex
        data_stream.write(struct.pack("i", data.get("sex", 0)))

        # Save character file data using KoikatuCharaData
        # This corresponds to ChaFileControl.SaveCharaFile in C#
        chara_data = data.get("character")
        if chara_data is not None:
            chara_bytes = bytes(chara_data)
            data_stream.write(chara_bytes)
        else:
            # If no character data, we need to write empty character data
            # This should not normally happen in valid data
            raise ValueError("Character data is missing in save_char_info")

        # Write bones dictionary
        bones = data.get("bones", {})
        data_stream.write(struct.pack("i", len(bones)))
        for bone_key, bone_data in bones.items():
            data_stream.write(struct.pack("i", bone_key))
            KoikatuSceneObjectLoader.save_bone_info(data_stream, bone_data)

        # Write IK targets dictionary
        ik_targets = data.get("ik_targets", {})
        data_stream.write(struct.pack("i", len(ik_targets)))
        for ik_key, ik_data in ik_targets.items():
            data_stream.write(struct.pack("i", ik_key))
            KoikatuSceneObjectLoader.save_bone_info(data_stream, ik_data)

        # Write child objects dictionary
        child = data.get("child", {})
        data_stream.write(struct.pack("i", len(child)))
        for child_key, child_list in child.items():
            data_stream.write(struct.pack("i", child_key))
            data_stream.write(struct.pack("i", len(child_list)))
            for child_obj in child_list:
                KoikatuSceneObjectLoader.save_child_objects(data_stream, child_obj, version)

        # Write kinematic mode
        data_stream.write(struct.pack("i", data.get("kinematic_mode", 0)))

        # Write anime info
        anime_info = data.get("anime_info", {})
        data_stream.write(struct.pack("i", anime_info.get("group", -1)))
        data_stream.write(struct.pack("i", anime_info.get("category", -1)))
        data_stream.write(struct.pack("i", anime_info.get("no", -1)))

        # Write hand patterns
        hand_patterns = data.get("hand_patterns", [0, 0])
        for i in range(2):
            data_stream.write(struct.pack("i", hand_patterns[i] if i < len(hand_patterns) else 0))

        # Write nipple
        data_stream.write(struct.pack("f", data.get("nipple", 0.0)))

        # Write siru (5 bytes)
        siru = data.get("siru", b"\x00" * 5)
        data_stream.write(siru if len(siru) == 5 else b"\x00" * 5)

        # Write mouth open
        data_stream.write(struct.pack("f", data.get("mouth_open", 0.0)))

        # Write lip sync
        data_stream.write(struct.pack("b", int(data.get("lip_sync", True))))

        # Write look at target (LookAtTargetInfo.Save - base.Save with _other=false)
        lookAtTarget = data.get("lookAtTarget", {})
        data_stream.write(struct.pack("i", lookAtTarget.get("dicKey", 0)))
        KoikatuSceneObjectLoader._save_vector3(data_stream, lookAtTarget.get("position", {"x": 0.0, "y": 0.0, "z": 0.0}))
        KoikatuSceneObjectLoader._save_vector3(data_stream, lookAtTarget.get("rotation", {"x": 0.0, "y": 0.0, "z": 0.0}))
        KoikatuSceneObjectLoader._save_vector3(data_stream, lookAtTarget.get("scale", {"x": 1.0, "y": 1.0, "z": 1.0}))

        # Write enable IK
        data_stream.write(struct.pack("b", int(data.get("enable_ik", False))))

        # Write active IK (5 bools)
        active_ik = data.get("active_ik", [True] * 5)
        for i in range(5):
            data_stream.write(struct.pack("b", int(active_ik[i] if i < len(active_ik) else True)))

        # Write enable FK
        data_stream.write(struct.pack("b", int(data.get("enable_fk", False))))

        # Write active FK (7 bools)
        active_fk = data.get("active_fk", [False, True, False, True, False, False, False])
        for i in range(7):
            data_stream.write(struct.pack("b", int(active_fk[i] if i < len(active_fk) else False)))

        # Write expression (4 for version < 0.0.9, 8 for version >= 0.0.9)
        expression_count = 8 if KoikatuSceneObjectLoader._compare_versions(version, "0.0.9") >= 0 else 4
        expression = data.get("expression", [False] * expression_count)
        for i in range(expression_count):
            data_stream.write(struct.pack("b", int(expression[i] if i < len(expression) else False)))

        # Write anime speed
        data_stream.write(struct.pack("f", data.get("anime_speed", 1.0)))

        # Write anime pattern
        data_stream.write(struct.pack("f", data.get("anime_pattern", 0.0)))

        # Write anime option visible
        data_stream.write(struct.pack("b", int(data.get("anime_option_visible", True))))

        # Write is anime force loop
        data_stream.write(struct.pack("b", int(data.get("is_anime_force_loop", False))))

        # Write voice ctrl (VoiceCtrl.Save)
        voiceCtrl = data.get("voiceCtrl", {})
        voice_list = voiceCtrl.get("list", [])
        data_stream.write(struct.pack("i", len(voice_list)))
        for voice_info in voice_list:
            data_stream.write(struct.pack("i", voice_info.get("group", 0)))
            data_stream.write(struct.pack("i", voice_info.get("category", 0)))
            data_stream.write(struct.pack("i", voice_info.get("no", 0)))
        data_stream.write(struct.pack("i", voiceCtrl.get("repeat", 0)))

        # Write visible son
        data_stream.write(struct.pack("b", int(data.get("visible_son", False))))

        # Write son length
        data_stream.write(struct.pack("f", data.get("son_length", 1.0)))

        # Write visible simple
        data_stream.write(struct.pack("b", int(data.get("visible_simple", False))))

        # Write simple color as JSON string
        simple_color = data.get("simple_color", {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0})
        KoikatuSceneObjectLoader._save_color_json(data_stream, simple_color)

        # Write anime option param (2 floats)
        anime_option_param = data.get("anime_option_param", [0.0, 0.0])
        for i in range(2):
            data_stream.write(struct.pack("f", anime_option_param[i] if i < len(anime_option_param) else 0.0))

        # Write neck byte data
        neck_byte_data = data.get("neck_byte_data", b"")
        data_stream.write(struct.pack("i", len(neck_byte_data)))
        data_stream.write(neck_byte_data)

        # Write eyes byte data
        eyes_byte_data = data.get("eyes_byte_data", b"")
        data_stream.write(struct.pack("i", len(eyes_byte_data)))
        data_stream.write(eyes_byte_data)

        # Write anime normalized time
        data_stream.write(struct.pack("f", data.get("anime_normalized_time", 0.0)))

        # Write dic access group
        dic_access_group = data.get("dic_access_group", {})
        data_stream.write(struct.pack("i", len(dic_access_group)))
        for key, value in dic_access_group.items():
            data_stream.write(struct.pack("i", key))
            data_stream.write(struct.pack("i", value))

        # Write dic access no
        dic_access_no = data.get("dic_access_no", {})
        data_stream.write(struct.pack("i", len(dic_access_no)))
        for key, value in dic_access_no.items():
            data_stream.write(struct.pack("i", key))
            data_stream.write(struct.pack("i", value))

    @staticmethod
    def save_item_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """Save item info data"""
        # Based on OIItemInfo.Save in C#
        data = obj_info["data"]

        # Save ObjectInfo base data
        KoikatuSceneObjectLoader._save_object_info_base(data_stream, data)

        # Write group, category, no
        data_stream.write(struct.pack("i", data["group"]))
        data_stream.write(struct.pack("i", data["category"]))
        data_stream.write(struct.pack("i", data["no"]))

        # Write anime pattern (version >= 1.1.1.0)
        if KoikatuSceneObjectLoader._compare_versions(version, "1.1.1.0") >= 0:
            data_stream.write(struct.pack("i", data["anime_pattern"]))

        # Write anime speed
        data_stream.write(struct.pack("f", data["anime_speed"]))

        # Write colors (version >= 0.0.3: 8 colors, else 7 colors)
        num_colors = 8 if KoikatuSceneObjectLoader._compare_versions(version, "0.0.3") >= 0 else 7
        for i in range(num_colors):
            color = data["colors"][i] if i < len(data["colors"]) else {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}
            write_string(data_stream, json.dumps(color, separators=(",", ":")).encode("utf-8"))

        # Write patterns
        for pattern in data["patterns"]:
            KoikatuSceneObjectLoader.save_pattern_info(data_stream, pattern)

        # Write alpha
        data_stream.write(struct.pack("f", data["alpha"]))

        # Write line color and width (version >= 0.0.4)
        if KoikatuSceneObjectLoader._compare_versions(version, "0.0.4") >= 0:
            write_string(data_stream, json.dumps(data["line_color"], separators=(",", ":")).encode("utf-8"))
            data_stream.write(struct.pack("f", data["line_width"]))

        # Write emission color, power, and light cancel (version >= 0.0.7)
        if KoikatuSceneObjectLoader._compare_versions(version, "0.0.7") >= 0:
            write_string(data_stream, json.dumps(data["emission_color"], separators=(",", ":")).encode("utf-8"))
            data_stream.write(struct.pack("f", data["emission_power"]))
            data_stream.write(struct.pack("f", data["light_cancel"]))

        # Write panel (version >= 0.0.6)
        if KoikatuSceneObjectLoader._compare_versions(version, "0.0.6") >= 0:
            KoikatuSceneObjectLoader.save_pattern_info(data_stream, data["panel"])

        # Write enable FK
        data_stream.write(struct.pack("b", int(data["enable_fk"])))

        # Write bones count
        data_stream.write(struct.pack("i", len(data["bones"])))

        # Write bones data
        for bone_key, bone_data in data["bones"].items():
            # Write bone key
            bone_key_bytes = bone_key.encode("utf-8")
            data_stream.write(struct.pack("i", len(bone_key_bytes)))
            data_stream.write(bone_key_bytes)

            # Write bone data
            KoikatuSceneObjectLoader.save_bone_info(data_stream, bone_data)

        # Write enable dynamic bone (version >= 1.0.1)
        if KoikatuSceneObjectLoader._compare_versions(version, "1.0.1") >= 0:
            data_stream.write(struct.pack("b", int(data["enable_dynamic_bone"])))

        # Write anime normalized time
        data_stream.write(struct.pack("f", data["anime_normalized_time"]))

        # Write child objects count
        data_stream.write(struct.pack("i", len(data.get("child", []))))

        # Write child objects data
        for child in data.get("child", []):
            KoikatuSceneObjectLoader.save_child_objects(data_stream, child, version)

    @staticmethod
    def save_light_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """Save light info data"""
        # Based on OILightInfo.Save in C#
        data = obj_info["data"]

        # Save ObjectInfo base data
        KoikatuSceneObjectLoader._save_object_info_base(data_stream, data)

        # Write no
        data_stream.write(struct.pack("i", data.get("no", 0)))

        # Write color (r, g, b, a)
        color = data.get("color", {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0})
        KoikatuSceneObjectLoader._save_color_rgba(data_stream, color)

        # Write intensity, range, spotAngle
        data_stream.write(struct.pack("f", data.get("intensity", 1.0)))
        data_stream.write(struct.pack("f", data.get("range", 10.0)))
        data_stream.write(struct.pack("f", data.get("spotAngle", 30.0)))

        # Write shadow, enable, drawTarget
        data_stream.write(struct.pack("b", int(data.get("shadow", True))))
        data_stream.write(struct.pack("b", int(data.get("enable", True))))
        data_stream.write(struct.pack("b", int(data.get("drawTarget", True))))

    @staticmethod
    def save_folder_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """Save folder info data"""
        # Based on OIFolderInfo.Save in C#
        data = obj_info["data"]

        # Save ObjectInfo base data
        KoikatuSceneObjectLoader._save_object_info_base(data_stream, data)

        # Write name (string)
        name = data.get("name", "")
        name_bytes = name.encode("utf-8") if isinstance(name, str) else name
        write_string(data_stream, name_bytes)

        # Write child count
        child_list = data.get("child", [])
        data_stream.write(struct.pack("i", len(child_list)))

        # Write each child object
        for child in child_list:
            KoikatuSceneObjectLoader.save_child_objects(data_stream, child, version)

    @staticmethod
    def save_route_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """Save route info data"""
        # Based on OIRouteInfo.Save in C#
        data = obj_info["data"]

        # Save ObjectInfo base data
        KoikatuSceneObjectLoader._save_object_info_base(data_stream, data)

        # Write name (string)
        name = data.get("name", "")
        name_bytes = name.encode("utf-8") if isinstance(name, str) else name
        write_string(data_stream, name_bytes)

        # Write child count and children
        child_list = data.get("child", [])
        data_stream.write(struct.pack("i", len(child_list)))
        for child in child_list:
            KoikatuSceneObjectLoader.save_child_objects(data_stream, child, version)

        # Write route count and route points
        route_list = data.get("route", [])
        data_stream.write(struct.pack("i", len(route_list)))
        for route_point in route_list:
            KoikatuSceneObjectLoader._save_route_point_info(data_stream, route_point)

        # Write active, loop, visibleLine
        data_stream.write(struct.pack("b", int(data.get("active", False))))
        data_stream.write(struct.pack("b", int(data.get("loop", True))))
        data_stream.write(struct.pack("b", int(data.get("visibleLine", True))))

        # Write orient (enum as int)
        data_stream.write(struct.pack("i", data.get("orient", 0)))

        # Write color as JSON string
        color = data.get("color", {"r": 0.0, "g": 0.0, "b": 1.0, "a": 1.0})
        KoikatuSceneObjectLoader._save_color_json(data_stream, color)

    @staticmethod
    def save_camera_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """Save camera info data"""
        # Based on OICameraInfo.Save in C#
        data = obj_info["data"]

        # Save ObjectInfo base data
        KoikatuSceneObjectLoader._save_object_info_base(data_stream, data)

        # Write name (string)
        name = data.get("name", "")
        name_bytes = name.encode("utf-8") if isinstance(name, str) else name
        write_string(data_stream, name_bytes)

        # Write active (boolean)
        data_stream.write(struct.pack("b", int(data.get("active", False))))

    @staticmethod
    def save_text_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """Save text info data"""
        # Based on OITextInfo.Save in C#
        data = obj_info["data"]

        # Save ObjectInfo base data
        KoikatuSceneObjectLoader._save_object_info_base(data_stream, data)

        # Write id
        data_stream.write(struct.pack("i", data.get("id", 0)))

        # Write color as JSON string
        color = data.get("color", {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0})
        KoikatuSceneObjectLoader._save_color_json(data_stream, color)

        # Write outlineColor as JSON string
        outline_color = data.get("outlineColor", {"r": 0.0, "g": 0.0, "b": 0.0, "a": 1.0})
        KoikatuSceneObjectLoader._save_color_json(data_stream, outline_color)

        # Write outlineSize
        data_stream.write(struct.pack("f", data.get("outlineSize", 1.0)))

        # Write textInfos (MessagePack serialized bytes)
        text_infos_bytes = data.get("textInfos_raw", b"")
        data_stream.write(struct.pack("i", len(text_infos_bytes)))
        data_stream.write(text_infos_bytes)

    # ============================================================
    # 7. CHILD OBJECT HANDLING
    # ============================================================
    """
    Child object handling methods.

    These methods handle recursive loading and saving of child objects.
    Many object types (characters, items, folders, routes) can contain
    nested child objects that need to be processed recursively.

    Methods follow the ObjectInfoAssist.LoadChild/SaveChild pattern from C#.
    """

    @staticmethod
    def load_child_objects(data_stream: BinaryIO, version: str = None) -> list:
        """
        Load child objects recursively
        Based on ObjectInfoAssist.LoadChild in C#
        """
        child_list = []

        # Read count of child objects
        count = struct.unpack("i", data_stream.read(4))[0]

        for obj_idx in range(count):
            # Read object type
            obj_type = struct.unpack("i", data_stream.read(4))[0]

            # Create object info based on type
            obj_info = {"type": obj_type, "data": {}}

            # Load object data based on type (recursively), passing version
            KoikatuSceneObjectLoader._dispatch_load(data_stream, obj_type, obj_info, version)

            child_list.append(obj_info)

        return child_list

    @staticmethod
    def save_child_objects(data_stream: BinaryIO, child_data: Dict[str, Any], version: str = None) -> None:
        """Save child object data (Note: Despite the plural name, this saves one object at a time)"""
        # Based on ObjectInfoAssist.LoadChild - dispatch based on type
        obj_type = child_data.get("type", -1)

        # Write object type
        data_stream.write(struct.pack("i", obj_type))

        # Dispatch to appropriate save function based on type
        KoikatuSceneObjectLoader._dispatch_save(data_stream, child_data, version)

    # ============================================================
    # 9. UTILITY METHODS
    # ============================================================
    """
    General utility methods used across multiple sections.

    - _compare_versions: Version string comparison for compatibility checks
    - _color_to_json: Color dictionary to JSON string conversion

    These methods provide common functionality needed by multiple loaders/savers.
    """

    @staticmethod
    def _compare_versions(version_str: str, target: str) -> int:
        """
        Compare version strings (e.g., "1.0.3.0" vs "1.0.4.0")
        Returns: -1 if version < target, 0 if equal, 1 if version > target
        """
        if version_str is None:
            # If no version provided, assume latest
            return 1

        version_parts = [int(x) for x in version_str.split(".")]
        target_parts = [int(x) for x in target.split(".")]

        # Pad shorter version with zeros
        while len(version_parts) < len(target_parts):
            version_parts.append(0)
        while len(target_parts) < len(version_parts):
            target_parts.append(0)

        for v, t in zip(version_parts, target_parts):
            if v < t:
                return -1
            elif v > t:
                return 1
        return 0

    @staticmethod
    def _color_to_json(color: Dict[str, float]) -> str:
        """Convert color dictionary to JSON string"""
        return json.dumps({"r": color.get("r", 0.0), "g": color.get("g", 0.0), "b": color.get("b", 0.0), "a": color.get("a", 1.0)}, separators=(",", ":"))
