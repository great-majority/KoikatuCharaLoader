# -*- coding:utf-8 -*-

import json
import struct
from typing import Dict, Any, BinaryIO

from kkloader.funcs import load_length, load_string, write_string
from kkloader.KoikatuCharaData import KoikatuCharaData


class KoikatuSceneObjectLoader:
    """
    Class for loading Koikatu scene object data.
    This is a Python implementation of the Studio.ObjectInfo.Load functions in C#.
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

        version_parts = [int(x) for x in version_str.split('.')]
        target_parts = [int(x) for x in target.split('.')]

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
    def load_char_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """Load character info data"""
        # Based on OICharInfo.Load in C#
        data = {}

        # Load ObjectInfo base data (base.Load in C#)
        # ObjectInfo.Load reads: dicKey, changeAmount, treeState, visible
        data["dicKey"] = struct.unpack("i", data_stream.read(4))[0]

        # Read changeAmount (position, rotation, scale)
        data["position"] = {
            "x": struct.unpack("f", data_stream.read(4))[0],
            "y": struct.unpack("f", data_stream.read(4))[0],
            "z": struct.unpack("f", data_stream.read(4))[0]
        }
        data["rotation"] = {
            "x": struct.unpack("f", data_stream.read(4))[0],
            "y": struct.unpack("f", data_stream.read(4))[0],
            "z": struct.unpack("f", data_stream.read(4))[0]
        }
        data["scale"] = {
            "x": struct.unpack("f", data_stream.read(4))[0],
            "y": struct.unpack("f", data_stream.read(4))[0],
            "z": struct.unpack("f", data_stream.read(4))[0]
        }
        data["treeState"] = struct.unpack("i", data_stream.read(4))[0]
        data["visible"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read sex
        data["sex"] = struct.unpack("i", data_stream.read(4))[0]

        # Load character file data using KoikatuCharaData
        # This corresponds to ChaFileControl.LoadCharaFile in C#
        # C# calls with noLoadPng: true, so contains_png=False
        try:
            # Debug: Check stream position before loading
            stream_pos_before = data_stream.tell()

            chara_data = KoikatuCharaData.load(data_stream, contains_png=False)
            data["character"] = chara_data

            stream_pos_after = data_stream.tell()
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
        data["anime_info"] = {
            "group": struct.unpack("i", data_stream.read(4))[0],
            "category": struct.unpack("i", data_stream.read(4))[0],
            "no": struct.unpack("i", data_stream.read(4))[0]
        }
        
        # Read hand patterns
        data["hand_patterns"] = [
            struct.unpack("i", data_stream.read(4))[0],
            struct.unpack("i", data_stream.read(4))[0]
        ]
        
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
            "position": {
                "x": struct.unpack("f", data_stream.read(4))[0],
                "y": struct.unpack("f", data_stream.read(4))[0],
                "z": struct.unpack("f", data_stream.read(4))[0]
            },
            "rotation": {
                "x": struct.unpack("f", data_stream.read(4))[0],
                "y": struct.unpack("f", data_stream.read(4))[0],
                "z": struct.unpack("f", data_stream.read(4))[0]
            },
            "scale": {
                "x": struct.unpack("f", data_stream.read(4))[0],
                "y": struct.unpack("f", data_stream.read(4))[0],
                "z": struct.unpack("f", data_stream.read(4))[0]
            }
        }
        
        # Read enable IK
        data["enable_ik"] = bool(struct.unpack("b", data_stream.read(1))[0])
        
        # Read active IK
        data["active_ik"] = []
        for _ in range(5):
            data["active_ik"].append(bool(struct.unpack("b", data_stream.read(1))[0]))
        
        # Read enable FK
        data["enable_fk"] = bool(struct.unpack("b", data_stream.read(1))[0])
        
        # Read active FK
        data["active_fk"] = []
        for _ in range(7):
            data["active_fk"].append(bool(struct.unpack("b", data_stream.read(1))[0]))
        
        # Read expression (4 for version < 0.0.9, 8 for version >= 0.0.9)
        expression_count = 8 if KoikatuSceneObjectLoader._compare_versions(version, "0.0.9") >= 0 else 4
        data["expression"] = []
        for _ in range(expression_count):
            data["expression"].append(bool(struct.unpack("b", data_stream.read(1))[0]))
        
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
        data["voiceCtrl"] = {
            "list": [],
            "repeat": None
        }
        for _ in range(voice_list_count):
            voice_info = {
                "group": struct.unpack("i", data_stream.read(4))[0],
                "category": struct.unpack("i", data_stream.read(4))[0],
                "no": struct.unpack("i", data_stream.read(4))[0]
            }
            data["voiceCtrl"]["list"].append(voice_info)
        data["voiceCtrl"]["repeat"] = struct.unpack("i", data_stream.read(4))[0]
        
        # Read visible son
        data["visible_son"] = bool(struct.unpack("b", data_stream.read(1))[0])
        
        # Read son length
        data["son_length"] = struct.unpack("f", data_stream.read(4))[0]
        
        # Read visible simple
        data["visible_simple"] = bool(struct.unpack("b", data_stream.read(1))[0])
        
        # Read simple color
        simple_color_json = load_length(data_stream, "b").decode('utf-8')
        try:
            data["simple_color"] = KoikatuSceneObjectLoader.parse_color_json(simple_color_json)
        except ValueError as e:
            print(f"Warning: Error parsing simple color JSON: {str(e)}")
            data["simple_color"] = {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}
        
        # Read anime option param
        data["anime_option_param"] = [
            struct.unpack("f", data_stream.read(4))[0],
            struct.unpack("f", data_stream.read(4))[0]
        ]
        
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
        data = {}

        # Load ObjectInfo base data
        data["dicKey"] = struct.unpack("i", data_stream.read(4))[0]
        data["position"] = {
            "x": struct.unpack("f", data_stream.read(4))[0],
            "y": struct.unpack("f", data_stream.read(4))[0],
            "z": struct.unpack("f", data_stream.read(4))[0]
        }
        data["rotation"] = {
            "x": struct.unpack("f", data_stream.read(4))[0],
            "y": struct.unpack("f", data_stream.read(4))[0],
            "z": struct.unpack("f", data_stream.read(4))[0]
        }
        data["scale"] = {
            "x": struct.unpack("f", data_stream.read(4))[0],
            "y": struct.unpack("f", data_stream.read(4))[0],
            "z": struct.unpack("f", data_stream.read(4))[0]
        }
        data["treeState"] = struct.unpack("i", data_stream.read(4))[0]
        data["visible"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read group, category, no
        data["group"] = struct.unpack("i", data_stream.read(4))[0]
        data["category"] = struct.unpack("i", data_stream.read(4))[0]
        data["no"] = struct.unpack("i", data_stream.read(4))[0]

        # Read anime pattern (version >= 1.1.1.0)
        if KoikatuSceneObjectLoader._compare_versions(version, "1.1.1.0") >= 0:
            data["anime_pattern"] = struct.unpack("i", data_stream.read(4))[0]

        # Read anime speed
        data["anime_speed"] = struct.unpack("f", data_stream.read(4))[0]

        # Read colors (version dependent)
        data["colors"] = []
        if KoikatuSceneObjectLoader._compare_versions(version, "0.0.3") >= 0:
            # Version >= 0.0.3: read 8 colors
            for _ in range(8):
                color_bytes = load_string(data_stream)
                if len(color_bytes) > 0:
                    data["colors"].append(json.loads(color_bytes.decode('utf-8')))
                else:
                    data["colors"].append(None)
        else:
            # Version < 0.0.3: read 7 colors
            for _ in range(7):
                color_bytes = load_string(data_stream)
                if len(color_bytes) > 0:
                    data["colors"].append(json.loads(color_bytes.decode('utf-8')))
                else:
                    data["colors"].append(None)
        
        # Read patterns
        data["patterns"] = []
        for _ in range(3):
            pattern_data = KoikatuSceneObjectLoader.load_pattern_info(data_stream)
            data["patterns"].append(pattern_data)
        
        # Read alpha
        data["alpha"] = struct.unpack("f", data_stream.read(4))[0]

        # Read line color and width (version >= 0.0.4)
        if KoikatuSceneObjectLoader._compare_versions(version, "0.0.4") >= 0:
            line_color_json = load_string(data_stream).decode('utf-8')
            data["line_color"] = json.loads(line_color_json)
            data["line_width"] = struct.unpack("f", data_stream.read(4))[0]

        # Read emission color, power, and light cancel (version >= 0.0.7)
        if KoikatuSceneObjectLoader._compare_versions(version, "0.0.7") >= 0:
            emission_color_json = load_string(data_stream).decode('utf-8')
            data["emission_color"] = json.loads(emission_color_json)
            data["emission_power"] = struct.unpack("f", data_stream.read(4))[0]
            data["light_cancel"] = struct.unpack("f", data_stream.read(4))[0]

        # Read panel (version >= 0.0.6)
        if KoikatuSceneObjectLoader._compare_versions(version, "0.0.6") >= 0:
            data["panel"] = KoikatuSceneObjectLoader.load_pattern_info(data_stream)
        
        # Read enable FK
        data["enable_fk"] = bool(struct.unpack("b", data_stream.read(1))[0])
        
        # Read bones count
        bones_count = struct.unpack("i", data_stream.read(4))[0]
        data["bones"] = {}

        # Read bones data (Dictionary<string, OIBoneInfo>)
        for _ in range(bones_count):
            # C# BinaryReader.ReadString() uses 7-bit encoded length
            bone_key = load_string(data_stream).decode('utf-8')
            bone_data = KoikatuSceneObjectLoader.load_bone_info(data_stream)
            data["bones"][bone_key] = bone_data
        
        # Read enable dynamic bone (version >= 1.0.1)
        if KoikatuSceneObjectLoader._compare_versions(version, "1.0.1") >= 0:
            data["enable_dynamic_bone"] = bool(struct.unpack("b", data_stream.read(1))[0])

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
        data = {}

        # Load ObjectInfo base data
        data["dicKey"] = struct.unpack("i", data_stream.read(4))[0]
        data["position"] = {
            "x": struct.unpack("f", data_stream.read(4))[0],
            "y": struct.unpack("f", data_stream.read(4))[0],
            "z": struct.unpack("f", data_stream.read(4))[0]
        }
        data["rotation"] = {
            "x": struct.unpack("f", data_stream.read(4))[0],
            "y": struct.unpack("f", data_stream.read(4))[0],
            "z": struct.unpack("f", data_stream.read(4))[0]
        }
        data["scale"] = {
            "x": struct.unpack("f", data_stream.read(4))[0],
            "y": struct.unpack("f", data_stream.read(4))[0],
            "z": struct.unpack("f", data_stream.read(4))[0]
        }
        data["treeState"] = struct.unpack("i", data_stream.read(4))[0]
        data["visible"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read light-specific data
        data["no"] = struct.unpack("i", data_stream.read(4))[0]

        # Read color (Utility.LoadColor - 4 floats: r, g, b, a)
        data["color"] = {
            "r": struct.unpack("f", data_stream.read(4))[0],
            "g": struct.unpack("f", data_stream.read(4))[0],
            "b": struct.unpack("f", data_stream.read(4))[0],
            "a": struct.unpack("f", data_stream.read(4))[0]
        }

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
        data = {}

        # Load ObjectInfo base data
        data["position"] = {
            "x": struct.unpack("f", data_stream.read(4))[0],
            "y": struct.unpack("f", data_stream.read(4))[0],
            "z": struct.unpack("f", data_stream.read(4))[0]
        }
        data["rotation"] = {
            "x": struct.unpack("f", data_stream.read(4))[0],
            "y": struct.unpack("f", data_stream.read(4))[0],
            "z": struct.unpack("f", data_stream.read(4))[0]
        }
        data["scale"] = {
            "x": struct.unpack("f", data_stream.read(4))[0],
            "y": struct.unpack("f", data_stream.read(4))[0],
            "z": struct.unpack("f", data_stream.read(4))[0]
        }
        data["treeState"] = struct.unpack("i", data_stream.read(4))[0]
        data["visible"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read folder name
        name_bytes = load_string(data_stream)
        data["name"] = name_bytes.decode('utf-8')

        # Load child objects recursively
        data["child"] = KoikatuSceneObjectLoader.load_child_objects(data_stream, version)

        obj_info["data"] = data
    
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
            "position": {
                "x": struct.unpack("f", data_stream.read(4))[0],
                "y": struct.unpack("f", data_stream.read(4))[0],
                "z": struct.unpack("f", data_stream.read(4))[0]
            },
            "rotation": {
                "x": struct.unpack("f", data_stream.read(4))[0],
                "y": struct.unpack("f", data_stream.read(4))[0],
                "z": struct.unpack("f", data_stream.read(4))[0]
            },
            "scale": {
                "x": struct.unpack("f", data_stream.read(4))[0],
                "y": struct.unpack("f", data_stream.read(4))[0],
                "z": struct.unpack("f", data_stream.read(4))[0]
            }
        }

        # Read isInit
        aid_info["isInit"] = bool(struct.unpack("b", data_stream.read(1))[0])

        return aid_info

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
        route_point["changeAmount"] = {
            "position": {
                "x": struct.unpack("f", data_stream.read(4))[0],
                "y": struct.unpack("f", data_stream.read(4))[0],
                "z": struct.unpack("f", data_stream.read(4))[0]
            },
            "rotation": {
                "x": struct.unpack("f", data_stream.read(4))[0],
                "y": struct.unpack("f", data_stream.read(4))[0],
                "z": struct.unpack("f", data_stream.read(4))[0]
            },
            "scale": {
                "x": struct.unpack("f", data_stream.read(4))[0],
                "y": struct.unpack("f", data_stream.read(4))[0],
                "z": struct.unpack("f", data_stream.read(4))[0]
            }
        }

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
    def load_route_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """
        Load route info data with full version-specific handling
        Based on OIRouteInfo.Load in C# (lines 65-91)
        """
        data = {}

        # Load ObjectInfo base data
        data["position"] = {
            "x": struct.unpack("f", data_stream.read(4))[0],
            "y": struct.unpack("f", data_stream.read(4))[0],
            "z": struct.unpack("f", data_stream.read(4))[0]
        }
        data["rotation"] = {
            "x": struct.unpack("f", data_stream.read(4))[0],
            "y": struct.unpack("f", data_stream.read(4))[0],
            "z": struct.unpack("f", data_stream.read(4))[0]
        }
        data["scale"] = {
            "x": struct.unpack("f", data_stream.read(4))[0],
            "y": struct.unpack("f", data_stream.read(4))[0],
            "z": struct.unpack("f", data_stream.read(4))[0]
        }
        data["treeState"] = struct.unpack("i", data_stream.read(4))[0]
        data["visible"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read route name
        name_bytes = load_string(data_stream)
        data["name"] = name_bytes.decode('utf-8')

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
            color_json = load_string(data_stream).decode('utf-8')
            data["color"] = json.loads(color_json)

        obj_info["data"] = data
    
    @staticmethod
    def load_camera_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """
        Load camera info data
        Based on OICameraInfo.Load in C#
        """
        data = {}

        # Load ObjectInfo base data
        data["position"] = {
            "x": struct.unpack("f", data_stream.read(4))[0],
            "y": struct.unpack("f", data_stream.read(4))[0],
            "z": struct.unpack("f", data_stream.read(4))[0]
        }
        data["rotation"] = {
            "x": struct.unpack("f", data_stream.read(4))[0],
            "y": struct.unpack("f", data_stream.read(4))[0],
            "z": struct.unpack("f", data_stream.read(4))[0]
        }
        data["scale"] = {
            "x": struct.unpack("f", data_stream.read(4))[0],
            "y": struct.unpack("f", data_stream.read(4))[0],
            "z": struct.unpack("f", data_stream.read(4))[0]
        }
        data["treeState"] = struct.unpack("i", data_stream.read(4))[0]
        data["visible"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read camera-specific data
        name_bytes = load_string(data_stream)
        data["name"] = name_bytes.decode('utf-8')
        data["active"] = bool(struct.unpack("b", data_stream.read(1))[0])

        obj_info["data"] = data
    
    @staticmethod
    def load_text_info(data_stream: BinaryIO, obj_info: Dict[str, Any], version: str = None) -> None:
        """
        Load text info data
        Based on OITextInfo.Load in C#
        """
        data = {}

        # Load ObjectInfo base data
        data["position"] = {
            "x": struct.unpack("f", data_stream.read(4))[0],
            "y": struct.unpack("f", data_stream.read(4))[0],
            "z": struct.unpack("f", data_stream.read(4))[0]
        }
        data["rotation"] = {
            "x": struct.unpack("f", data_stream.read(4))[0],
            "y": struct.unpack("f", data_stream.read(4))[0],
            "z": struct.unpack("f", data_stream.read(4))[0]
        }
        data["scale"] = {
            "x": struct.unpack("f", data_stream.read(4))[0],
            "y": struct.unpack("f", data_stream.read(4))[0],
            "z": struct.unpack("f", data_stream.read(4))[0]
        }
        data["treeState"] = struct.unpack("i", data_stream.read(4))[0]
        data["visible"] = bool(struct.unpack("b", data_stream.read(1))[0])

        # Read text-specific data
        data["id"] = struct.unpack("i", data_stream.read(4))[0]

        # Read colors
        color_json = load_string(data_stream).decode('utf-8')
        data["color"] = json.loads(color_json)

        outline_color_json = load_string(data_stream).decode('utf-8')
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
        bone_data["changeAmount"] = {
            "position": {
                "x": struct.unpack("f", data_stream.read(4))[0],
                "y": struct.unpack("f", data_stream.read(4))[0],
                "z": struct.unpack("f", data_stream.read(4))[0]
            },
            "rotation": {
                "x": struct.unpack("f", data_stream.read(4))[0],
                "y": struct.unpack("f", data_stream.read(4))[0],
                "z": struct.unpack("f", data_stream.read(4))[0]
            },
            "scale": {
                "x": struct.unpack("f", data_stream.read(4))[0],
                "y": struct.unpack("f", data_stream.read(4))[0],
                "z": struct.unpack("f", data_stream.read(4))[0]
            }
        }

        return bone_data

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
            obj_info = {
                "type": obj_type,
                "data": {}
            }

            # Load object data based on type (recursively), passing version
            if obj_type == 0:  # OICharInfo
                KoikatuSceneObjectLoader.load_char_info(data_stream, obj_info, version)
            elif obj_type == 1:  # OIItemInfo
                KoikatuSceneObjectLoader.load_item_info(data_stream, obj_info, version)
            elif obj_type == 2:  # OILightInfo
                KoikatuSceneObjectLoader.load_light_info(data_stream, obj_info, version)
            elif obj_type == 3:  # OIFolderInfo
                KoikatuSceneObjectLoader.load_folder_info(data_stream, obj_info, version)
            elif obj_type == 4:  # OIRouteInfo
                KoikatuSceneObjectLoader.load_route_info(data_stream, obj_info, version)
            elif obj_type == 5:  # OICameraInfo
                KoikatuSceneObjectLoader.load_camera_info(data_stream, obj_info, version)
            elif obj_type == 7:  # OITextInfo
                KoikatuSceneObjectLoader.load_text_info(data_stream, obj_info, version)
            else:
                # Unknown type - this should not happen
                print(f"Warning: Unknown object type {obj_type}")

            child_list.append(obj_info)

        return child_list

    
    @staticmethod
    def load_pattern_info(data_stream: BinaryIO) -> Dict[str, Any]:
        """Load pattern info data"""
        # Based on PatternInfo.Load in C#
        pattern_data = {}
        
        # Read key
        pattern_data["key"] = struct.unpack("i", data_stream.read(4))[0]
        
        # Read filePath using load_string
        file_path_bytes = load_string(data_stream)
        pattern_data["file_path"] = file_path_bytes.decode('utf-8')
        
        # Read clamp
        pattern_data["clamp"] = bool(struct.unpack("b", data_stream.read(1))[0])
        
        # Read uv (Vector4)
        uv_json = load_string(data_stream).decode('utf-8')
        pattern_data["uv"] = json.loads(uv_json)
        
        # Read rot
        pattern_data["rot"] = struct.unpack("f", data_stream.read(4))[0]
        
        return pattern_data
    
    @staticmethod
    def save_item_info(data_stream: BinaryIO, obj_info: Dict[str, Any]) -> None:
        """Save item info data"""
        # Based on OIItemInfo.Save in C#
        data = obj_info["data"]
        
        # Save ObjectInfo base data
        KoikatuSceneObjectLoader.save_object_info_base(data_stream, data)
        data_stream.write(struct.pack("i", 0))
        
        # Write group, category, no
        data_stream.write(struct.pack("i", data["group"]))
        data_stream.write(struct.pack("i", data["category"]))
        data_stream.write(struct.pack("i", data["no"]))
        
        # Write anime pattern
        data_stream.write(struct.pack("i", data["anime_pattern"]))
        
        # Write anime speed
        data_stream.write(struct.pack("f", data["anime_speed"]))
        
        # Write colors
        for color in data["colors"]:
            KoikatuSceneObjectLoader._write_string(data_stream, json.dumps(color).encode('utf-8'))
        
        # Write patterns
        for pattern in data["patterns"]:
            KoikatuSceneObjectLoader.save_pattern_info(data_stream, pattern)
        
        # Write alpha
        data_stream.write(struct.pack("f", data["alpha"]))
        
        # Write line color
        KoikatuSceneObjectLoader._write_string(data_stream, json.dumps(data["line_color"]).encode('utf-8'))
        
        # Write line width
        data_stream.write(struct.pack("f", data["line_width"]))
        
        # Write emission color
        KoikatuSceneObjectLoader._write_string(data_stream, json.dumps(data["emission_color"]).encode('utf-8'))
        
        # Write emission power
        data_stream.write(struct.pack("f", data["emission_power"]))
        
        # Write light cancel
        data_stream.write(struct.pack("f", data["light_cancel"]))
        
        # Write panel
        KoikatuSceneObjectLoader.save_pattern_info(data_stream, data["panel"])
        
        # Write enable FK
        data_stream.write(struct.pack("b", int(data["enable_fk"])))
        
        # Write bones count
        data_stream.write(struct.pack("i", len(data["bones"])))
        
        # Write bones data
        for bone_key, bone_data in data["bones"].items():
            # Write bone key
            bone_key_bytes = bone_key.encode('utf-8')
            data_stream.write(struct.pack("i", len(bone_key_bytes)))
            data_stream.write(bone_key_bytes)
            
            # Write bone data
            KoikatuSceneObjectLoader.save_bone_info(data_stream, bone_data)
        
        # Write enable dynamic bone
        data_stream.write(struct.pack("b", int(data["enable_dynamic_bone"])))
        
        # Write anime normalized time
        data_stream.write(struct.pack("f", data["anime_normalized_time"]))
        
        # Write child objects count
        data_stream.write(struct.pack("i", len(data.get("child", []))))
        
        # Write child objects data
        for child in data.get("child", []):
            KoikatuSceneObjectLoader.save_child_object(data_stream, child)
    
    @staticmethod
    def save_object_info_base(data_stream: BinaryIO, data: Dict[str, Any]) -> None:
        """Save ObjectInfo base data (ObjectInfo.Save)"""
        # Save dicKey, changeAmount (position, rotation, scale), treeState, visible
        
        # Write position (Vector3)
        pos = data.get("position", {"x": 0.0, "y": 0.0, "z": 0.0})
        data_stream.write(struct.pack("f", pos.get("x", 0.0)))
        data_stream.write(struct.pack("f", pos.get("y", 0.0)))
        data_stream.write(struct.pack("f", pos.get("z", 0.0)))
        
        # Write rotation (Vector3)
        rot = data.get("rotation", {"x": 0.0, "y": 0.0, "z": 0.0})
        data_stream.write(struct.pack("f", rot.get("x", 0.0)))
        data_stream.write(struct.pack("f", rot.get("y", 0.0)))
        data_stream.write(struct.pack("f", rot.get("z", 0.0)))
        
        # Write scale (Vector3)
        scale = data.get("scale", {"x": 1.0, "y": 1.0, "z": 1.0})
        data_stream.write(struct.pack("f", scale.get("x", 1.0)))
        data_stream.write(struct.pack("f", scale.get("y", 1.0)))
        data_stream.write(struct.pack("f", scale.get("z", 1.0)))
        
        # Write treeState
        data_stream.write(struct.pack("i", data.get("treeState", 0)))
        
        # Write visible
        data_stream.write(struct.pack("b", int(data.get("visible", True))))
    
    @staticmethod
    def save_pattern_info(data_stream: BinaryIO, pattern_data: Dict[str, Any]) -> None:
        """Save pattern info data"""
        # Based on PatternInfo.Save in C#
        
        # Write key
        data_stream.write(struct.pack("i", pattern_data["key"]))
        
        # Write filePath
        KoikatuSceneObjectLoader._write_string(data_stream, pattern_data["file_path"].encode('utf-8'))
        
        # Write clamp
        data_stream.write(struct.pack("b", int(pattern_data["clamp"])))
        
        # Write uv (Vector4)
        KoikatuSceneObjectLoader._write_string(data_stream, json.dumps(pattern_data["uv"]).encode('utf-8'))
        
        # Write rot
        data_stream.write(struct.pack("f", pattern_data["rot"]))
    
    @staticmethod
    def save_bone_info(data_stream: BinaryIO, bone_data: Dict[str, Any]) -> None:
        """Save bone info data"""
        # This is a placeholder implementation
        # In a real implementation, we would use actual data from the bone
        KoikatuSceneObjectLoader.save_object_info_base(data_stream, bone_data)
    
    @staticmethod
    def save_child_object(data_stream: BinaryIO, child_data: Dict[str, Any]) -> None:
        """Save child object data"""
        # This is a placeholder implementation
        # In a real implementation, we would use actual data from the child object
        KoikatuSceneObjectLoader.save_object_info_base(data_stream, child_data)
    
    @staticmethod
    def save_char_info(data_stream: BinaryIO, obj_info: Dict[str, Any]) -> None:
        """Save character info data"""
        raise NotImplementedError("save_char_info is not implemented")
    
    @staticmethod
    def save_light_info(data_stream: BinaryIO, obj_info: Dict[str, Any]) -> None:
        """Save light info data"""
        raise NotImplementedError("save_light_info is not implemented")
    
    @staticmethod
    def save_folder_info(data_stream: BinaryIO, obj_info: Dict[str, Any]) -> None:
        """Save folder info data"""
        raise NotImplementedError("save_folder_info is not implemented")
    
    @staticmethod
    def save_route_info(data_stream: BinaryIO, obj_info: Dict[str, Any]) -> None:
        """Save route info data"""
        raise NotImplementedError("save_route_info is not implemented")
    
    @staticmethod
    def save_camera_info(data_stream: BinaryIO, obj_info: Dict[str, Any]) -> None:
        """Save camera info data"""
        raise NotImplementedError("save_camera_info is not implemented")
    
    @staticmethod
    def save_text_info(data_stream: BinaryIO, obj_info: Dict[str, Any]) -> None:
        """Save text info data"""
        raise NotImplementedError("save_text_info is not implemented")
    
    @staticmethod
    def _write_string(data_stream: BinaryIO, value: bytes) -> None:
        """
        Write a string to the data stream using the same format as load_string
        Using write_string from funcs.py
        """
        write_string(data_stream, value)
    
    @staticmethod
    def parse_color_json(json_str: str) -> Dict[str, float]:
        """Parse color from JSON string"""
        # JSONとして解析
        color_data = json.loads(json_str)
        return {
            "r": color_data.get("r", 0),
            "g": color_data.get("g", 0),
            "b": color_data.get("b", 0),
            "a": color_data.get("a", 1.0)
        }
