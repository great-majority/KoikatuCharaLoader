# -*- coding:utf-8 -*-

import json
import struct
from typing import Dict, Any, BinaryIO

from kkloader.funcs import load_length, load_string, get_png, write_string


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
        data_stream.read(4)

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
            color_bytes = load_string(data_stream)
            data["colors"].append(json.loads(color_bytes.decode('utf-8')))
        
        # Read patterns
        data["patterns"] = []
        for _ in range(3):
            pattern_data = KoikatuSceneObjectLoader.load_pattern_info(data_stream)
            data["patterns"].append(pattern_data)
        
        # Read alpha
        data["alpha"] = struct.unpack("f", data_stream.read(4))[0]
        
        # Read line color
        line_color_json = load_string(data_stream).decode('utf-8')
        data["line_color"] = json.loads(line_color_json)
        
        # Read line width
        data["line_width"] = struct.unpack("f", data_stream.read(4))[0]
        
        # Read emission color
        emission_color_json = load_string(data_stream).decode('utf-8')
        data["emission_color"] = json.loads(emission_color_json)
        
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
        """Save ObjectInfo base data"""
        # This is a placeholder implementation based on the skip_object_info_base method
        # In a real implementation, we would use actual data from the object
        
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
