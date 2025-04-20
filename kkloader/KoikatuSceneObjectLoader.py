# -*- coding:utf-8 -*-

import json
import struct
from typing import Dict, Any, BinaryIO

from kkloader.funcs import load_length, load_string, get_png


class KoikatuSceneObjectLoader:
    """
    Class for loading Koikatu scene object data.
    This is a Python implementation of the Studio.ObjectInfo.Load functions in C#.
    """
    
    @staticmethod
    def load_char_info(data_stream: BinaryIO, obj_info: Dict[str, Any]) -> None:
        """Load character info data"""
        # Based on OICharInfo.Load in C#
        data = {}
        
        # Read sex
        data["sex"] = struct.unpack("i", data_stream.read(4))[0]
        
        # Skip character file data for now (would need to implement ChaFileControl.LoadCharaFile)
        # In a real implementation, we would parse the character file data
        # For now, we'll just skip it by reading the PNG data
        try:
            char_png = get_png(data_stream)
            data["char_png_size"] = len(char_png)
        except Exception as e:
            print(f"Warning: Error reading character PNG data: {str(e)}")
            data["char_png_size"] = 0
        
        # Read bones count
        bones_count = struct.unpack("i", data_stream.read(4))[0]
        data["bones"] = {}
        
        # Read bones data
        for _ in range(bones_count):
            bone_key = struct.unpack("i", data_stream.read(4))[0]
            # Skip bone data for now
            # In a real implementation, we would parse the bone data
            data["bones"][bone_key] = {"key": bone_key}
            # Skip the rest of the bone data
            KoikatuSceneObjectLoader.skip_bone_info(data_stream)
        
        # Read IK targets count
        ik_count = struct.unpack("i", data_stream.read(4))[0]
        data["ik_targets"] = {}
        
        # Read IK targets data
        for _ in range(ik_count):
            ik_key = struct.unpack("i", data_stream.read(4))[0]
            # Skip IK target data for now
            # In a real implementation, we would parse the IK target data
            data["ik_targets"][ik_key] = {"key": ik_key}
            # Skip the rest of the IK target data
            KoikatuSceneObjectLoader.skip_ik_target_info(data_stream)
        
        # Read child objects count
        child_count = struct.unpack("i", data_stream.read(4))[0]
        data["child"] = {}
        
        # Read child objects data
        for _ in range(child_count):
            child_key = struct.unpack("i", data_stream.read(4))[0]
            child_obj_count = struct.unpack("i", data_stream.read(4))[0]
            # Skip child objects data for now
            # In a real implementation, we would parse the child objects data
            data["child"][child_key] = {"count": child_obj_count}
            # Skip the rest of the child objects data
            KoikatuSceneObjectLoader.skip_child_objects(data_stream, child_obj_count)
        
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
        
        # Skip look at target info for now
        KoikatuSceneObjectLoader.skip_look_at_target_info(data_stream)
        
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
        
        # Read expression
        data["expression"] = []
        for _ in range(8):
            data["expression"].append(bool(struct.unpack("b", data_stream.read(1))[0]))
        
        # Read anime speed
        data["anime_speed"] = struct.unpack("f", data_stream.read(4))[0]
        
        # Read anime pattern
        data["anime_pattern"] = struct.unpack("f", data_stream.read(4))[0]
        
        # Read anime option visible
        data["anime_option_visible"] = bool(struct.unpack("b", data_stream.read(1))[0])
        
        # Read is anime force loop
        data["is_anime_force_loop"] = bool(struct.unpack("b", data_stream.read(1))[0])
        
        # Skip voice ctrl for now
        KoikatuSceneObjectLoader.skip_voice_ctrl(data_stream)
        
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
    def load_item_info(data_stream: BinaryIO, obj_info: Dict[str, Any]) -> None:
        """Load item info data"""
        # Based on OIItemInfo.Load in C#
        data = {}
        
        # Skip ObjectInfo base data
        KoikatuSceneObjectLoader.skip_object_info_base(data_stream)
        
        # Read group, category, no
        data["group"] = struct.unpack("i", data_stream.read(4))[0]
        data["category"] = struct.unpack("i", data_stream.read(4))[0]
        data["no"] = struct.unpack("i", data_stream.read(4))[0]
        
        # Read anime pattern
        data["anime_pattern"] = struct.unpack("i", data_stream.read(4))[0]
        
        # Read anime speed
        data["anime_speed"] = struct.unpack("f", data_stream.read(4))[0]
        
        # Read colors
        data["colors"] = []
        for _ in range(8):
            try:
                color_bytes = load_string(data_stream)
                
                # 先頭の文字が文字列の長さを示している場合、それを取り除く
                if color_bytes and len(color_bytes) > 1:
                    # 先頭の文字を取り除く
                    color_bytes_without_prefix = color_bytes[1:]
                    
                    # JSONとして解析
                    try:
                        color_json = color_bytes_without_prefix.decode('utf-8')
                        # カンマが抜けている場合があるので、追加する
                        color_json = color_json.replace('"g"', '"g":').replace('"b"', '"b":').replace('"a"', '"a":')
                        data["colors"].append(json.loads("{" + color_json))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        # デコードに失敗した場合は、デフォルトの色を追加
                        data["colors"].append({"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0})
                else:
                    # デフォルトの色を追加
                    data["colors"].append({"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0})
            except Exception:
                # エラーが発生した場合は、デフォルトの色を追加
                data["colors"].append({"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0})
        
        # Read patterns
        data["patterns"] = []
        for _ in range(3):
            pattern_data = KoikatuSceneObjectLoader.load_pattern_info(data_stream)
            data["patterns"].append(pattern_data)
        
        # Read alpha
        data["alpha"] = struct.unpack("f", data_stream.read(4))[0]
        
        # Read line color
        line_color_json = load_string(data_stream).decode('utf-8')
        try:
            data["line_color"] = json.loads(line_color_json)
        except json.JSONDecodeError:
            data["line_color"] = {"r": 0.0, "g": 0.0, "b": 0.0, "a": 1.0}
        
        # Read line width
        data["line_width"] = struct.unpack("f", data_stream.read(4))[0]
        
        # Read emission color
        emission_color_json = load_string(data_stream).decode('utf-8')
        try:
            data["emission_color"] = json.loads(emission_color_json)
        except json.JSONDecodeError:
            data["emission_color"] = {"r": 0.0, "g": 0.0, "b": 0.0, "a": 1.0}
        
        # Read emission power
        data["emission_power"] = struct.unpack("f", data_stream.read(4))[0]
        
        # Read light cancel
        data["light_cancel"] = struct.unpack("f", data_stream.read(4))[0]
        
        # Read panel
        data["panel"] = KoikatuSceneObjectLoader.load_pattern_info(data_stream)
        
        # Read enable FK
        data["enable_fk"] = bool(struct.unpack("b", data_stream.read(1))[0])
        
        # Read bones count
        bones_count = struct.unpack("i", data_stream.read(4))[0]
        data["bones"] = {}
        
        # Read bones data
        for _ in range(bones_count):
            bone_key_length = struct.unpack("i", data_stream.read(4))[0]
            bone_key = data_stream.read(bone_key_length).decode('utf-8')
            # Skip bone data for now
            # In a real implementation, we would parse the bone data
            data["bones"][bone_key] = {"key": bone_key}
            # Skip the rest of the bone data
            KoikatuSceneObjectLoader.skip_bone_info(data_stream)
        
        # Read enable dynamic bone
        data["enable_dynamic_bone"] = bool(struct.unpack("b", data_stream.read(1))[0])
        
        # Read anime normalized time
        data["anime_normalized_time"] = struct.unpack("f", data_stream.read(4))[0]
        
        # Read child objects count
        child_count = struct.unpack("i", data_stream.read(4))[0]
        data["child"] = []
        
        # Skip child objects data for now
        # In a real implementation, we would parse the child objects data
        KoikatuSceneObjectLoader.skip_child_objects(data_stream, child_count)
        
        obj_info["data"] = data
    
    @staticmethod
    def load_light_info(data_stream: BinaryIO, obj_info: Dict[str, Any]) -> None:
        """Load light info data"""
        obj_info["data"] = {"type": "light"}
    
    @staticmethod
    def load_folder_info(data_stream: BinaryIO, obj_info: Dict[str, Any]) -> None:
        """Load folder info data"""
        obj_info["data"] = {"type": "folder"}
    
    @staticmethod
    def load_route_info(data_stream: BinaryIO, obj_info: Dict[str, Any]) -> None:
        """Load route info data"""
        obj_info["data"] = {"type": "route"}
    
    @staticmethod
    def load_camera_info(data_stream: BinaryIO, obj_info: Dict[str, Any]) -> None:
        """Load camera info data"""
        obj_info["data"] = {"type": "camera"}
    
    @staticmethod
    def load_text_info(data_stream: BinaryIO, obj_info: Dict[str, Any]) -> None:
        """Load text info data"""
        obj_info["data"] = {"type": "text"}
    
    @staticmethod
    def skip_bone_info(data_stream: BinaryIO) -> None:
        """Skip bone info data"""
        # Skip ObjectInfo base data
        KoikatuSceneObjectLoader.skip_object_info_base(data_stream)
    
    @staticmethod
    def skip_ik_target_info(data_stream: BinaryIO) -> None:
        """Skip IK target info data"""
        # Skip ObjectInfo base data
        KoikatuSceneObjectLoader.skip_object_info_base(data_stream)
    
    @staticmethod
    def skip_object_info_base(data_stream: BinaryIO) -> None:
        """Skip ObjectInfo base data"""
        # Skip position
        data_stream.read(12)  # 3 floats (x, y, z)
        
        # Skip rotation
        data_stream.read(12)  # 3 floats (x, y, z)
        
        # Skip scale
        data_stream.read(12)  # 3 floats (x, y, z)
        
        # Skip treeState
        data_stream.read(4)  # 1 int
        
        # Skip visible
        data_stream.read(1)  # 1 bool
    
    @staticmethod
    def skip_child_objects(data_stream: BinaryIO, count: int) -> None:
        """Skip child objects data"""
        for _ in range(count):
            # Skip ObjectInfo
            KoikatuSceneObjectLoader.skip_object_info_base(data_stream)
    
    @staticmethod
    def skip_look_at_target_info(data_stream: BinaryIO) -> None:
        """Skip look at target info data"""
        # Skip ObjectInfo base data
        KoikatuSceneObjectLoader.skip_object_info_base(data_stream)
        
        # Skip target type
        data_stream.read(4)  # 1 int
        
        # Skip target number
        data_stream.read(4)  # 1 int
    
    @staticmethod
    def skip_voice_ctrl(data_stream: BinaryIO) -> None:
        """Skip voice ctrl data"""
        # Skip play
        data_stream.read(1)  # 1 bool
        
        # Skip repeat
        data_stream.read(4)  # 1 int
        
        # Skip no
        data_stream.read(4)  # 1 int
    
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
        try:
            uv_json = load_string(data_stream).decode('utf-8')
            pattern_data["uv"] = json.loads(uv_json)
        except Exception:
            # エラーが発生した場合は、デフォルトの値を設定
            pattern_data["uv"] = {"x": 0.0, "y": 0.0, "z": 1.0, "w": 1.0}
        
        # Read rot
        pattern_data["rot"] = struct.unpack("f", data_stream.read(4))[0]
        
        return pattern_data
    
    @staticmethod
    def parse_color_json(json_str: str) -> Dict[str, float]:
        """Parse color from JSON string"""
        try:
            # JSONとして解析
            color_data = json.loads(json_str)
            return {
                "r": color_data.get("r", 0),
                "g": color_data.get("g", 0),
                "b": color_data.get("b", 0),
                "a": color_data.get("a", 1.0)
            }
        except json.JSONDecodeError as e:
            # JSONとして解析できない場合はエラーを発生させる
            raise ValueError(f"Invalid JSON color data: {json_str[:30]}... Error: {str(e)}")
