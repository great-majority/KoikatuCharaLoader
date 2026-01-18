import json
import struct
from typing import Any, BinaryIO, Dict

from kkloader.AicomiCharaData import AicomiCharaData
from kkloader.funcs import load_length, load_string, load_type, write_string
from kkloader.HoneycomeCharaData import HoneycomeCharaData
from kkloader.SummerVacationCharaData import SummerVacationCharaData


class HoneycomeSceneObjectLoader:
    """
    Class for loading Honeycome scene object data.
    This implementation supports only Item (type=1) and Folder (type=3) objects.
    """

    # ============================================================
    # 1. DISPATCH TABLES & CONFIGURATION
    # ============================================================
    """
    Object type dispatching system.

    Maps object type IDs to their respective load/save handler methods.
    Supported object types:
      1: Item (OIItemInfo)
      3: Folder (OIFolderInfo)
    """

    # Object type dispatch tables
    _LOAD_DISPATCH = {
        0: "load_char_info",
        1: "load_item_info",
        2: "load_light_info",
        3: "load_folder_info",
        4: "load_route_info",
        5: "load_camera_info",
    }

    _SAVE_DISPATCH = {
        0: "save_char_info",
        1: "save_item_info",
        2: "save_light_info",
        3: "save_folder_info",
        4: "save_route_info",
        5: "save_camera_info",
    }

    # Character data class dispatch based on header string
    _CHARA_DATA_DISPATCH = {
        b"\xe3\x80\x90HCPChara\xe3\x80\x91": HoneycomeCharaData,  # 【HCPChara】 - Honeycome Party
        b"\xe3\x80\x90HCChara\xe3\x80\x91": HoneycomeCharaData,  # 【HCChara】 - Honeycome
        b"\xe3\x80\x90SVChara\xe3\x80\x91": SummerVacationCharaData,  # 【SVChara】 - SummerVacationScramble
        b"\xe3\x80\x90ACChara\xe3\x80\x91": AicomiCharaData,  # 【ACChara】 - Aicomi
    }

    @staticmethod
    def _get_chara_data_class(data_stream: BinaryIO):
        """
        Read the header from the data stream to determine the appropriate CharaData class.
        Returns the class and restores the stream position.
        """
        start_pos = data_stream.tell()

        # Read header (same as KoikatuCharaData._load_header, but only what we need)
        # product_no (int) + header string (length-prefixed with byte length)
        _product_no = load_type(data_stream, "i")
        header = load_length(data_stream, "b")

        # Restore stream position
        data_stream.seek(start_pos)

        # Look up the class based on header
        chara_class = HoneycomeSceneObjectLoader._CHARA_DATA_DISPATCH.get(header)
        if chara_class is None:
            raise ValueError(f"Unknown character header: {header}")

        return chara_class

    @staticmethod
    def _dispatch_load(data_stream: BinaryIO, obj_type: int, obj_info: Dict[str, Any], version: str = None) -> None:
        """Dispatch to appropriate load method based on object type"""
        method_name = HoneycomeSceneObjectLoader._LOAD_DISPATCH.get(obj_type)
        if method_name is None:
            raise ValueError(f"Unknown object type: {obj_type}")
        method = getattr(HoneycomeSceneObjectLoader, method_name)
        method(data_stream, obj_info, version)

    @staticmethod
    def _dispatch_save(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """Dispatch to appropriate save method based on object type"""
        obj_type = obj_info.get("type", -1)
        method_name = HoneycomeSceneObjectLoader._SAVE_DISPATCH.get(obj_type)
        if method_name is None:
            raise ValueError(f"Unknown object type: {obj_type}")
        method = getattr(HoneycomeSceneObjectLoader, method_name)
        method(data_stream, obj_info, version)

    # ============================================================
    # 2. PRIMITIVE TYPE HELPERS
    # ============================================================
    """
    Low-level data structure helpers for binary serialization.

    These methods handle the most basic data types used throughout
    the scene file format: Vector3, Color (RGBA/JSON), and boolean arrays.
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
    def parse_color_json(json_str: str) -> Dict[str, float]:
        """Parse color from JSON string"""
        color_data = json.loads(json_str)
        return {"r": color_data.get("r", 0), "g": color_data.get("g", 0), "b": color_data.get("b", 0), "a": color_data.get("a", 1.0)}

    @staticmethod
    def _save_color_json(data_stream: BinaryIO, color: Dict[str, float]) -> None:
        """Save Color as JSON string with length prefix"""
        color_bytes = json.dumps(color, separators=(",", ":")).encode("utf-8")
        write_string(data_stream, color_bytes)

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
    """

    @staticmethod
    def _load_object_info_base(data_stream: BinaryIO) -> Dict[str, Any]:
        """Load ObjectInfo base data (dicKey, position, rotation, scale, treeState, visible)"""
        return {
            "dicKey": struct.unpack("i", data_stream.read(4))[0],
            "position": HoneycomeSceneObjectLoader._load_vector3(data_stream),
            "rotation": HoneycomeSceneObjectLoader._load_vector3(data_stream),
            "scale": HoneycomeSceneObjectLoader._load_vector3(data_stream),
            "treeState": struct.unpack("i", data_stream.read(4))[0],
            "visible": bool(struct.unpack("b", data_stream.read(1))[0]),
        }

    @staticmethod
    def _save_object_info_base(data_stream: BinaryIO, data: Dict[str, Any]) -> None:
        """Save ObjectInfo base data (ObjectInfo.Save)"""
        # Write dicKey (int)
        data_stream.write(struct.pack("i", data.get("dicKey", 0)))

        # Write position (Vector3)
        pos = data.get("position", {"x": 0.0, "y": 0.0, "z": 0.0})
        HoneycomeSceneObjectLoader._save_vector3(data_stream, pos, default=0.0)

        # Write rotation (Vector3)
        rot = data.get("rotation", {"x": 0.0, "y": 0.0, "z": 0.0})
        HoneycomeSceneObjectLoader._save_vector3(data_stream, rot, default=0.0)

        # Write scale (Vector3)
        scale = data.get("scale", {"x": 1.0, "y": 1.0, "z": 1.0})
        HoneycomeSceneObjectLoader._save_vector3(data_stream, scale, default=1.0)

        # Write treeState
        data_stream.write(struct.pack("i", data.get("treeState", 0)))

        # Write visible
        data_stream.write(struct.pack("b", int(data.get("visible", True))))

    # ============================================================
    # 4. COMPONENT DATA HELPERS
    # ============================================================
    """
    Component-level data structure handlers.

    These methods handle complex sub-components that are used by multiple object types:
    - BoneInfo: FK/IK bone data for items
    - PatternInfo: Texture pattern data for items (Honeycome version)
    """

    @staticmethod
    def load_bone_info(data_stream: BinaryIO) -> Dict[str, Any]:
        """
        Load bone info data
        Based on OIBoneInfo.Save/Load in C#
        """
        bone_data = {}

        # Read dicKey (int)
        bone_data["dicKey"] = struct.unpack("i", data_stream.read(4))[0]

        # Read ChangeAmount (ChangeAmount.Load/Save in C#)
        # ChangeAmount contains 3 Vector3: position, rotation, scale
        bone_data["changeAmount"] = {"position": HoneycomeSceneObjectLoader._load_vector3(data_stream), "rotation": HoneycomeSceneObjectLoader._load_vector3(data_stream), "scale": HoneycomeSceneObjectLoader._load_vector3(data_stream)}

        return bone_data

    @staticmethod
    def save_bone_info(data_stream: BinaryIO, bone_data: Dict[str, Any]) -> None:
        """Save bone info data"""
        # Write dicKey
        data_stream.write(struct.pack("i", bone_data.get("dicKey", 0)))

        # Write changeAmount (position, rotation, scale)
        change_amount = bone_data.get("changeAmount", {})
        HoneycomeSceneObjectLoader._save_vector3(data_stream, change_amount.get("position", {"x": 0.0, "y": 0.0, "z": 0.0}))
        HoneycomeSceneObjectLoader._save_vector3(data_stream, change_amount.get("rotation", {"x": 0.0, "y": 0.0, "z": 0.0}))
        HoneycomeSceneObjectLoader._save_vector3(data_stream, change_amount.get("scale", {"x": 1.0, "y": 1.0, "z": 1.0}))

    @staticmethod
    def load_pattern_info(data_stream: BinaryIO) -> Dict[str, Any]:
        """Load pattern info data (Honeycome version)"""
        pattern_data = {}

        # Read unknown float (always 1.0?)
        pattern_data["unknown_float"] = struct.unpack("f", data_stream.read(4))[0]

        # Read key
        pattern_data["key"] = struct.unpack("i", data_stream.read(4))[0]

        if pattern_data["key"] == -1:
            pattern_data["pattern_filepath"] = load_string(data_stream).decode("utf-8")
            pattern_data["unknown_bool"] = bool(struct.unpack("b", data_stream.read(1))[0])

        else:
            pattern_data["clamp"] = bool(struct.unpack("b", data_stream.read(1))[0])
            pattern_data["unknown_bool"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read uv (Vector4)
        uv_json = load_string(data_stream).decode("utf-8")
        pattern_data["uv"] = json.loads(uv_json)

        return pattern_data

    @staticmethod
    def save_pattern_info(data_stream: BinaryIO, pattern_data: Dict[str, Any]) -> None:
        """Save pattern info data (Honeycome version)"""
        # Write unknown float
        data_stream.write(struct.pack("f", pattern_data.get("unknown_float", 1.0)))

        # Write key
        data_stream.write(struct.pack("i", pattern_data["key"]))

        if pattern_data["key"] == -1:
            # Write pattern_filepath
            write_string(data_stream, pattern_data.get("pattern_filepath", "").encode("utf-8"))
            # Write unknown bool
            data_stream.write(struct.pack("b", int(pattern_data.get("unknown_bool", False))))
        else:
            # Write clamp
            data_stream.write(struct.pack("b", int(pattern_data["clamp"])))
            # Write unknown bool
            data_stream.write(struct.pack("b", int(pattern_data.get("unknown_bool", False))))

        # Write uv (Vector4)
        write_string(data_stream, json.dumps(pattern_data["uv"], separators=(",", ":")).encode("utf-8"))

    @staticmethod
    def _load_route_point_info(data_stream: BinaryIO, version: str = None) -> Dict[str, Any]:
        """
        Load OIRoutePointInfo data with version-specific handling
        Based on OIRoutePointInfo.Load in C#
        """
        route_point = {}

        # Read dicKey
        route_point["dicKey"] = struct.unpack("i", data_stream.read(4))[0]

        # Read ChangeAmount (3 Vector3)
        route_point["changeAmount"] = {
            "position": HoneycomeSceneObjectLoader._load_vector3(data_stream),
            "rotation": HoneycomeSceneObjectLoader._load_vector3(data_stream),
            "scale": HoneycomeSceneObjectLoader._load_vector3(data_stream),
        }

        route_point["speed"] = struct.unpack("f", data_stream.read(4))[0]
        route_point["easeType"] = struct.unpack("i", data_stream.read(4))[0]
        route_point["connection"] = struct.unpack("i", data_stream.read(4))[0]
        route_point["aidInfo"] = HoneycomeSceneObjectLoader._load_route_point_aid_info(data_stream)
        route_point["link"] = bool(struct.unpack("b", data_stream.read(1))[0])

        return route_point

    @staticmethod
    def _save_route_point_info(data_stream: BinaryIO, route_point: Dict[str, Any], version: str = None) -> None:
        """
        Save OIRoutePointInfo data
        Based on OIRoutePointInfo.Save in C#
        """
        # Write dicKey
        data_stream.write(struct.pack("i", route_point.get("dicKey", 0)))

        # Write ChangeAmount (3 Vector3: position, rotation, scale)
        change_amount = route_point.get("changeAmount", {})
        HoneycomeSceneObjectLoader._save_vector3(data_stream, change_amount.get("position", {"x": 0.0, "y": 0.0, "z": 0.0}))
        HoneycomeSceneObjectLoader._save_vector3(data_stream, change_amount.get("rotation", {"x": 0.0, "y": 0.0, "z": 0.0}))
        HoneycomeSceneObjectLoader._save_vector3(data_stream, change_amount.get("scale", {"x": 1.0, "y": 1.0, "z": 1.0}))

        # Write speed
        data_stream.write(struct.pack("f", route_point.get("speed", 2.0)))

        # Write easeType
        data_stream.write(struct.pack("i", route_point.get("easeType", 0)))

        # Write connection
        data_stream.write(struct.pack("i", route_point.get("connection", 0)))

        # Write aidInfo
        aid_info = route_point.get("aidInfo", {})
        HoneycomeSceneObjectLoader._save_route_point_aid_info(data_stream, aid_info)

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
        aid_info["changeAmount"] = {
            "position": HoneycomeSceneObjectLoader._load_vector3(data_stream),
            "rotation": HoneycomeSceneObjectLoader._load_vector3(data_stream),
            "scale": HoneycomeSceneObjectLoader._load_vector3(data_stream),
        }

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
        HoneycomeSceneObjectLoader._save_vector3(data_stream, change_amount.get("position", {"x": 0.0, "y": 0.0, "z": 0.0}))
        HoneycomeSceneObjectLoader._save_vector3(data_stream, change_amount.get("rotation", {"x": 0.0, "y": 0.0, "z": 0.0}))
        HoneycomeSceneObjectLoader._save_vector3(data_stream, change_amount.get("scale", {"x": 1.0, "y": 1.0, "z": 1.0}))

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
    - load_camera_info: Camera objects (OICameraInfo)

    All methods populate the obj_info dictionary with loaded data.
    """

    @staticmethod
    def load_char_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """Load character info data"""
        # Based on OICharInfo.Load in C#
        # Load ObjectInfo base data (dicKey, position, rotation, scale, treeState, visible)
        data = HoneycomeSceneObjectLoader._load_object_info_base(data_stream)

        # Read sex
        data["sex"] = struct.unpack("i", data_stream.read(4))[0]

        # Load character file data using appropriate CharaData class based on header
        # This corresponds to ChaFileControl.LoadCharaFile in C#
        # C# calls with noLoadPng: true, so contains_png=False
        try:
            # Determine the appropriate CharaData class based on header
            chara_class = HoneycomeSceneObjectLoader._get_chara_data_class(data_stream)
            chara_data = chara_class.load(data_stream, contains_png=False)
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
            bone_data = HoneycomeSceneObjectLoader.load_bone_info(data_stream)
            data["bones"][bone_key] = bone_data

        # Read IK targets count
        ik_count = struct.unpack("i", data_stream.read(4))[0]
        data["ik_targets"] = {}

        # Read IK targets data (OIIKTargetInfo extends OIBoneInfo)
        for _ in range(ik_count):
            ik_key = struct.unpack("i", data_stream.read(4))[0]
            ik_data = HoneycomeSceneObjectLoader.load_bone_info(data_stream)
            data["ik_targets"][ik_key] = ik_data

        # Read child objects count (Dictionary<int, List<ObjectInfo>>)
        child_count = struct.unpack("i", data_stream.read(4))[0]
        data["child"] = {}

        # Read child objects data for each key
        for child_idx in range(child_count):
            child_key = struct.unpack("i", data_stream.read(4))[0]
            # Load child objects recursively for this key
            data["child"][child_key] = HoneycomeSceneObjectLoader.load_child_objects(data_stream, version)

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

        data["unknown_bytes_1"] = data_stream.read(4)

        # Read look at target info (LookAtTargetInfo.Load)
        # base.Load with _other=false: only dicKey and changeAmount, no treeState/visible
        data["lookAtTarget"] = {
            "dicKey": struct.unpack("i", data_stream.read(4))[0],
            "position": HoneycomeSceneObjectLoader._load_vector3(data_stream),
            "rotation": HoneycomeSceneObjectLoader._load_vector3(data_stream),
            "scale": HoneycomeSceneObjectLoader._load_vector3(data_stream),
        }

        data["unknown_bytes_2"] = data_stream.read(14)

        # Read enable IK
        data["enable_ik"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read active IK
        data["active_ik"] = HoneycomeSceneObjectLoader._load_bool_array(data_stream, 5)

        # Read enable FK
        data["enable_fk"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read active FK
        data["active_fk"] = HoneycomeSceneObjectLoader._load_bool_array(data_stream, 7)

        # Read expression
        expression_count = 9
        data["expression"] = HoneycomeSceneObjectLoader._load_bool_array(data_stream, expression_count)

        # Read anime speed
        data["anime_speed"] = struct.unpack("f", data_stream.read(4))[0]

        # Read anime pattern
        data["anime_pattern"] = struct.unpack("f", data_stream.read(4))[0]

        # Read anime option visible
        data["anime_option_visible"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read is anime force loop
        data["is_anime_force_loop"] = bool(struct.unpack("b", data_stream.read(1))[0])

        data["unknown_int_1"] = struct.unpack("i", data_stream.read(4))[0]
        data["unknown_int_2"] = struct.unpack("i", data_stream.read(4))[0]

        # Read voice ctrl (VoiceCtrl.Load)
        voice_list_count = struct.unpack("i", data_stream.read(4))[0]
        data["voiceCtrl"] = {"list": [], "repeat": None}
        for _ in range(voice_list_count):
            voice_info = {"group": struct.unpack("i", data_stream.read(4))[0], "category": struct.unpack("i", data_stream.read(4))[0], "no": struct.unpack("i", data_stream.read(4))[0]}
            data["voiceCtrl"]["list"].append(voice_info)
        data["voiceCtrl"]["repeat"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read visible son
        data["visible_son"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read son length
        data["son_length"] = struct.unpack("f", data_stream.read(4))[0]

        # Read visible simple
        data["visible_simple"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read simple color
        simple_color_json = load_length(data_stream, "b").decode("utf-8")
        data["simple_color"] = HoneycomeSceneObjectLoader.parse_color_json(simple_color_json)

        # Read anime option param
        data["anime_option_param"] = [struct.unpack("f", data_stream.read(4))[0], struct.unpack("f", data_stream.read(4))[0]]

        # Read unknown int
        data["unknown_int_3"] = struct.unpack("i", data_stream.read(4))[0]

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
        data = HoneycomeSceneObjectLoader._load_object_info_base(data_stream)

        data["unknown_1"] = struct.unpack("i", data_stream.read(4))[0]
        data["group"] = struct.unpack("i", data_stream.read(4))[0]
        data["category"] = struct.unpack("i", data_stream.read(4))[0]
        data["no"] = struct.unpack("i", data_stream.read(4))[0]
        data["unknown_3"] = data_stream.read(8)

        data["colors"] = []
        for _ in range(8):
            color_bytes = load_string(data_stream)
            if len(color_bytes) > 0:
                data["colors"].append(json.loads(color_bytes.decode("utf-8")))
            else:
                data["colors"].append(None)

        data["unknown_4"] = struct.unpack("i", data_stream.read(4))[0]
        data["unknown_5"] = bool(struct.unpack("b", data_stream.read(1))[0])

        data["patterns"] = []
        for _ in range(3):
            data["patterns"].append(HoneycomeSceneObjectLoader.load_pattern_info(data_stream))

        data["unknown_6"] = data_stream.read(4)
        data["alpha"] = struct.unpack("f", data_stream.read(4))[0]

        line_color_json = load_string(data_stream).decode("utf-8")
        data["line_color"] = json.loads(line_color_json)
        data["line_width"] = struct.unpack("f", data_stream.read(4))[0]

        emission_color_json = load_string(data_stream).decode("utf-8")
        data["emission_color"] = json.loads(emission_color_json)
        data["emission_power"] = struct.unpack("f", data_stream.read(4))[0]
        data["light_cancel"] = struct.unpack("f", data_stream.read(4))[0]

        data["unknown_7"] = data_stream.read(6)
        data["unknown_8"] = load_string(data_stream).decode("utf-8")
        data["unknown_9"] = data_stream.read(4)

        data["enable_fk"] = bool(struct.unpack("b", data_stream.read(1))[0])

        bones_count = struct.unpack("i", data_stream.read(4))[0]
        data["bones"] = {}
        for _ in range(bones_count):
            bone_key = load_string(data_stream).decode("utf-8")
            data["bones"][bone_key] = HoneycomeSceneObjectLoader.load_bone_info(data_stream)

        data["unknown_10"] = bool(struct.unpack("b", data_stream.read(1))[0])
        data["anime_normalized_time"] = struct.unpack("f", data_stream.read(4))[0]
        data["child"] = HoneycomeSceneObjectLoader.load_child_objects(data_stream, version)
        obj_info["data"] = data

    @staticmethod
    def load_folder_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """Load folder info data"""
        # Load ObjectInfo base data
        data = HoneycomeSceneObjectLoader._load_object_info_base(data_stream)

        # Read folder name
        name_bytes = load_string(data_stream)
        data["name"] = name_bytes.decode("utf-8")

        # Load child objects recursively
        data["child"] = HoneycomeSceneObjectLoader.load_child_objects(data_stream, version)

        obj_info["data"] = data

    @staticmethod
    def load_light_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """
        Load light info data
        Based on OILightInfo.Load in C#
        """
        # Load ObjectInfo base data (dicKey, position, rotation, scale, treeState, visible)
        data = HoneycomeSceneObjectLoader._load_object_info_base(data_stream)

        # Read light-specific data
        data["no"] = struct.unpack("i", data_stream.read(4))[0]

        data["unknown_bytes"] = data_stream.read(2)  # 0x0101
        color_bytes = load_string(data_stream)
        data["color"] = HoneycomeSceneObjectLoader.parse_color_json(color_bytes.decode("utf-8"))

        # Read light/shadow settings
        data["intensity"] = struct.unpack("f", data_stream.read(4))[0]
        data["range"] = struct.unpack("f", data_stream.read(4))[0]
        data["outsideSpotAngle"] = struct.unpack("f", data_stream.read(4))[0]
        data["insideSpotAngle"] = struct.unpack("f", data_stream.read(4))[0]
        data["shadow"] = bool(struct.unpack("b", data_stream.read(1))[0])
        data["shadowStrength"] = struct.unpack("f", data_stream.read(4))[0]

        obj_info["data"] = data

    @staticmethod
    def load_route_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """
        Load route info data with full version-specific handling
        Based on OIRouteInfo.Load in C#
        """
        # Load ObjectInfo base data (dicKey, position, rotation, scale, treeState, visible)
        data = HoneycomeSceneObjectLoader._load_object_info_base(data_stream)

        # Read route name
        name_bytes = load_string(data_stream)
        data["name"] = name_bytes.decode("utf-8")

        # Load child objects recursively
        data["child"] = HoneycomeSceneObjectLoader.load_child_objects(data_stream, version)

        # Read route points list
        route_points_count = struct.unpack("i", data_stream.read(4))[0]
        data["route_points"] = []
        for _ in range(route_points_count):
            route_point = HoneycomeSceneObjectLoader._load_route_point_info(data_stream, version)
            data["route_points"].append(route_point)

        data["active"] = bool(struct.unpack("b", data_stream.read(1))[0])
        data["loop"] = bool(struct.unpack("b", data_stream.read(1))[0])
        data["visibleLine"] = bool(struct.unpack("b", data_stream.read(1))[0])
        data["orient"] = struct.unpack("i", data_stream.read(4))[0]

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
        data = HoneycomeSceneObjectLoader._load_object_info_base(data_stream)

        # Read camera-specific data
        name_bytes = load_string(data_stream)
        data["name"] = name_bytes.decode("utf-8")
        data["active"] = bool(struct.unpack("b", data_stream.read(1))[0])

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
    - save_camera_info: Camera objects (OICameraInfo)

    All methods write data from the obj_info dictionary to binary format.
    """

    @staticmethod
    def save_char_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """Save character info data"""
        # Based on OICharInfo.Save in C#
        data = obj_info["data"]

        # Save ObjectInfo base data
        HoneycomeSceneObjectLoader._save_object_info_base(data_stream, data)

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
            HoneycomeSceneObjectLoader.save_bone_info(data_stream, bone_data)

        # Write IK targets dictionary
        ik_targets = data.get("ik_targets", {})
        data_stream.write(struct.pack("i", len(ik_targets)))
        for ik_key, ik_data in ik_targets.items():
            data_stream.write(struct.pack("i", ik_key))
            HoneycomeSceneObjectLoader.save_bone_info(data_stream, ik_data)

        # Write child objects dictionary
        child = data.get("child", {})
        data_stream.write(struct.pack("i", len(child)))
        for child_key, child_list in child.items():
            data_stream.write(struct.pack("i", child_key))
            data_stream.write(struct.pack("i", len(child_list)))
            for child_obj in child_list:
                HoneycomeSceneObjectLoader.save_child_objects(data_stream, child_obj, version)

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

        # Write unknown bytes (4 bytes)
        data_stream.write(data["unknown_bytes_1"])

        # Write look at target (LookAtTargetInfo.Save - base.Save with _other=false)
        lookAtTarget = data.get("lookAtTarget", {})
        data_stream.write(struct.pack("i", lookAtTarget.get("dicKey", 0)))
        HoneycomeSceneObjectLoader._save_vector3(data_stream, lookAtTarget.get("position", {"x": 0.0, "y": 0.0, "z": 0.0}))
        HoneycomeSceneObjectLoader._save_vector3(data_stream, lookAtTarget.get("rotation", {"x": 0.0, "y": 0.0, "z": 0.0}))
        HoneycomeSceneObjectLoader._save_vector3(data_stream, lookAtTarget.get("scale", {"x": 1.0, "y": 1.0, "z": 1.0}))

        # Write unknown bytes (14 bytes)
        data_stream.write(data["unknown_bytes_2"])

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

        # Write expression
        expression_count = 9
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

        # Write unknown ints
        data_stream.write(struct.pack("i", data["unknown_int_1"]))
        data_stream.write(struct.pack("i", data["unknown_int_2"]))

        # Write voice ctrl (VoiceCtrl.Save)
        voiceCtrl = data.get("voiceCtrl", {})
        voice_list = voiceCtrl.get("list", [])
        data_stream.write(struct.pack("i", len(voice_list)))
        for voice_info in voice_list:
            data_stream.write(struct.pack("i", voice_info.get("group", 0)))
            data_stream.write(struct.pack("i", voice_info.get("category", 0)))
            data_stream.write(struct.pack("i", voice_info.get("no", 0)))
        data_stream.write(struct.pack("b", int(voiceCtrl.get("repeat", False))))

        # Write visible son
        data_stream.write(struct.pack("b", int(data.get("visible_son", False))))

        # Write son length
        data_stream.write(struct.pack("f", data.get("son_length", 1.0)))

        # Write visible simple
        data_stream.write(struct.pack("b", int(data.get("visible_simple", False))))

        # Write simple color as JSON string (1-byte length prefix)
        simple_color = data.get("simple_color", {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0})
        simple_color_bytes = json.dumps(simple_color, separators=(",", ":")).encode("utf-8")
        data_stream.write(struct.pack("b", len(simple_color_bytes)))
        data_stream.write(simple_color_bytes)

        # Write anime option param (2 floats)
        anime_option_param = data.get("anime_option_param", [0.0, 0.0])
        for i in range(2):
            data_stream.write(struct.pack("f", anime_option_param[i] if i < len(anime_option_param) else 0.0))

        # Write unknown int
        data_stream.write(struct.pack("i", data["unknown_int_3"]))

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
        data = obj_info["data"]
        HoneycomeSceneObjectLoader._save_object_info_base(data_stream, data)

        data_stream.write(struct.pack("i", data["unknown_1"]))
        data_stream.write(struct.pack("i", data["group"]))
        data_stream.write(struct.pack("i", data["category"]))
        data_stream.write(struct.pack("i", data["no"]))
        data_stream.write(data["unknown_3"])

        for i in range(8):
            color = data["colors"][i] if i < len(data["colors"]) and data["colors"][i] is not None else {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}
            write_string(data_stream, json.dumps(color, separators=(",", ":")).encode("utf-8"))

        data_stream.write(struct.pack("i", data["unknown_4"]))
        data_stream.write(struct.pack("b", int(data["unknown_5"])))

        for pattern in data["patterns"]:
            HoneycomeSceneObjectLoader.save_pattern_info(data_stream, pattern)

        data_stream.write(data["unknown_6"])
        data_stream.write(struct.pack("f", data["alpha"]))

        # Note: line_color/line_width exist since version >= 0.0.4 (always true for 0.0.5 and 1.0.0)
        write_string(
            data_stream,
            json.dumps(data["line_color"], separators=(",", ":")).encode("utf-8"),
        )
        data_stream.write(struct.pack("f", data["line_width"]))

        write_string(
            data_stream,
            json.dumps(data["emission_color"], separators=(",", ":")).encode("utf-8"),
        )
        data_stream.write(struct.pack("f", data["emission_power"]))
        data_stream.write(struct.pack("f", data["light_cancel"]))

        data_stream.write(data["unknown_7"])
        write_string(data_stream, data["unknown_8"].encode("utf-8"))
        data_stream.write(data["unknown_9"])

        data_stream.write(struct.pack("b", int(data["enable_fk"])))
        data_stream.write(struct.pack("i", len(data["bones"])))
        for bone_key, bone_data in data["bones"].items():
            write_string(data_stream, bone_key.encode("utf-8"))
            HoneycomeSceneObjectLoader.save_bone_info(data_stream, bone_data)

        data_stream.write(struct.pack("b", int(data["unknown_10"])))
        data_stream.write(struct.pack("f", data["anime_normalized_time"]))

        data_stream.write(struct.pack("i", len(data.get("child", []))))
        for child in data.get("child", []):
            HoneycomeSceneObjectLoader.save_child_objects(data_stream, child, version)

    @staticmethod
    def save_folder_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """Save folder info data"""
        data = obj_info["data"]

        # Save ObjectInfo base data
        HoneycomeSceneObjectLoader._save_object_info_base(data_stream, data)

        # Write name (string)
        name = data.get("name", "")
        name_bytes = name.encode("utf-8") if isinstance(name, str) else name
        write_string(data_stream, name_bytes)

        # Write child count
        child_list = data.get("child", [])
        data_stream.write(struct.pack("i", len(child_list)))

        # Write each child object
        for child in child_list:
            HoneycomeSceneObjectLoader.save_child_objects(data_stream, child, version)

    @staticmethod
    def save_light_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """Save light info data"""
        # Based on OILightInfo.Save in C#
        data = obj_info["data"]

        # Save ObjectInfo base data
        HoneycomeSceneObjectLoader._save_object_info_base(data_stream, data)

        # Write no
        data_stream.write(struct.pack("i", data.get("no", 0)))

        # Write unknown_bytes (2 bytes)
        data_stream.write(data["unknown_bytes"])

        # Write color as JSON string
        color = data.get("color", {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0})
        HoneycomeSceneObjectLoader._save_color_json(data_stream, color)

        # Write light/shadow settings
        data_stream.write(struct.pack("f", data.get("intensity", 1.0)))
        data_stream.write(struct.pack("f", data.get("range", 10.0)))
        data_stream.write(struct.pack("f", data.get("outsideSpotAngle", 30.0)))
        data_stream.write(struct.pack("f", data.get("insideSpotAngle", 30.0)))
        data_stream.write(struct.pack("b", int(data.get("shadow", True))))
        data_stream.write(struct.pack("f", data.get("shadowStrength", 1.0)))

    @staticmethod
    def save_route_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """Save route info data"""
        # Based on OIRouteInfo.Save in C#
        data = obj_info["data"]

        # Save ObjectInfo base data
        HoneycomeSceneObjectLoader._save_object_info_base(data_stream, data)

        # Write name (string)
        name = data.get("name", "")
        name_bytes = name.encode("utf-8") if isinstance(name, str) else name
        write_string(data_stream, name_bytes)

        # Write child count and children
        child_list = data.get("child", [])
        data_stream.write(struct.pack("i", len(child_list)))
        for child in child_list:
            HoneycomeSceneObjectLoader.save_child_objects(data_stream, child, version)

        # Write route points count and route points
        route_points = data.get("route_points", [])
        data_stream.write(struct.pack("i", len(route_points)))
        for route_point in route_points:
            HoneycomeSceneObjectLoader._save_route_point_info(data_stream, route_point, version)

        # Write active, loop, visibleLine
        data_stream.write(struct.pack("b", int(data.get("active", False))))
        data_stream.write(struct.pack("b", int(data.get("loop", True))))
        data_stream.write(struct.pack("b", int(data.get("visibleLine", True))))

        # Write orient
        data_stream.write(struct.pack("i", data.get("orient", 0)))

        # Write color as JSON string
        color = data.get("color", {"r": 0.0, "g": 0.0, "b": 1.0, "a": 1.0})
        HoneycomeSceneObjectLoader._save_color_json(data_stream, color)

    @staticmethod
    def save_camera_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """Save camera info data"""
        # Based on OICameraInfo.Save in C#
        data = obj_info["data"]

        # Save ObjectInfo base data
        HoneycomeSceneObjectLoader._save_object_info_base(data_stream, data)

        # Write name (string)
        name = data.get("name", "")
        name_bytes = name.encode("utf-8") if isinstance(name, str) else name
        write_string(data_stream, name_bytes)

        # Write active (boolean)
        data_stream.write(struct.pack("b", int(data.get("active", False))))

    # ============================================================
    # 7. CHILD OBJECT HANDLING
    # ============================================================
    """
    Child object handling methods.

    These methods handle recursive loading and saving of child objects.
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

            # Load object data based on type (recursively)
            HoneycomeSceneObjectLoader._dispatch_load(data_stream, obj_type, obj_info, version)

            child_list.append(obj_info)

        return child_list

    @staticmethod
    def save_child_objects(data_stream: BinaryIO, child_data: Dict[str, Any], version: str = None) -> None:
        """Save child object data"""
        obj_type = child_data.get("type", -1)

        # Write object type
        data_stream.write(struct.pack("i", obj_type))

        # Dispatch to appropriate save function based on type
        HoneycomeSceneObjectLoader._dispatch_save(data_stream, child_data, version)

