# -*- coding:utf-8 -*-

import io
import json
import struct
from typing import Union

from kkloader.funcs import get_png, load_length, load_string, load_type, msg_unpack


class KoikatuSceneData:
    """
    Class for loading and parsing Koikatu scene data.
    This is a Python implementation of the Studio.SceneInfo.Load function in C#.
    """
    def __init__(self):
        self.image = None
        self.version = None
        self.dataVersion = None
        self.dicObject = {}
        self.map = -1
        self.caMap = {}
        self.sunLightType = 0
        self.mapOption = True
        self.aceNo = 0
        self.aceBlend = 0.0
        self.enableAOE = True
        self.aoeColor = {"r": 180/255, "g": 180/255, "b": 180/255, "a": 1.0}
        self.aoeRadius = 0.1
        self.enableBloom = True
        self.bloomIntensity = 0.4
        self.bloomBlur = 0.8
        self.bloomThreshold = 0.6
        self.enableDepth = False
        self.depthFocalSize = 0.95
        self.depthAperture = 0.6
        self.enableVignette = True
        self.enableFog = False
        self.fogColor = {"r": 137/255, "g": 193/255, "b": 221/255, "a": 1.0}
        self.fogHeight = 1.0
        self.fogStartDistance = 0.0
        self.enableSunShafts = False
        self.sunThresholdColor = {"r": 128/255, "g": 128/255, "b": 128/255, "a": 1.0}
        self.sunColor = {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}
        self.sunCaster = -1
        self.enableShadow = True
        self.faceNormal = False
        self.faceShadow = False
        self.lineColorG = 0.0
        self.ambientShadow = {"r": 128/255, "g": 128/255, "b": 128/255, "a": 1.0}
        self.lineWidthG = 0.0
        self.rampG = 0
        self.ambientShadowG = 0.0
        self.shaderType = 0
        self.skyInfo = {"Enable": False, "Pattern": 0}
        self.cameraSaveData = None
        self.cameraData = []
        self.charaLight = {}
        self.mapLight = {}
        self.bgmCtrl = {"play": False, "repeat": 0, "no": 0}
        self.envCtrl = {"play": False, "repeat": 0, "no": 0}
        self.outsideSoundCtrl = {"play": False, "repeat": 0, "fileName": ""}
        self.background = ""
        self.frame = ""

    @classmethod
    def load(cls, filelike: Union[str, bytes, io.BytesIO], safe_mode: bool = True) -> 'KoikatuSceneData':
        """
        Load Koikatu scene data from a file or bytes.
        
        Args:
            filelike: Path to the file, bytes, or BytesIO object containing the scene data
            
        Returns:
            KoikatuSceneData: The loaded scene data
        """
        ks = cls()

        if isinstance(filelike, str):
            with open(filelike, "br") as f:
                data = f.read()
            data_stream = io.BytesIO(data)
        elif isinstance(filelike, bytes):
            data_stream = io.BytesIO(filelike)
        elif isinstance(filelike, io.BytesIO):
            data_stream = filelike
        else:
            raise ValueError(f"Unsupported input type: {type(filelike)}")

        try:
            # Skip PNG header and data
            ks.image = get_png(data_stream)
        except Exception as e:
            if not safe_mode:
                raise
            print(f"Warning: Error reading PNG data: {str(e)}")
            # Try to reset the stream position to the beginning
            data_stream.seek(0)
        
        # Read version
        try:
            version_bytes = load_length(data_stream, "b")
            version_str = version_bytes.decode('utf-8')
        except UnicodeDecodeError:
            # If we can't decode as UTF-8, try to extract version string using regex
            import re
            version_match = re.search(b'([0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+)', version_bytes)
            if version_match:
                version_str = version_match.group(1).decode('ascii')
            else:
                # Default version if we can't extract it
                version_str = "1.0.0.0"
            print(f"Warning: Could not decode version string as UTF-8, extracted: {version_str}")
        
        ks.version = version_str
        ks.dataVersion = version_str
        
        # Read object dictionary
        obj_count = load_type(data_stream, "i")
        for i in range(obj_count):
            key = load_type(data_stream, "i")
            obj_type = load_type(data_stream, "i")
            
            # Create object info based on type
            obj_info = {
                "type": obj_type,
                "data": {}
            }
            
            # Load object data (simplified - we're not fully implementing all object types)
            # In a complete implementation, we would create specific object classes for each type
            # and load their data properly
            if obj_type == 0:  # OICharInfo
                ks._load_char_info(data_stream, obj_info)
            elif obj_type == 1:  # OIItemInfo
                ks._load_item_info(data_stream, obj_info)
            elif obj_type == 2:  # OILightInfo
                ks._load_light_info(data_stream, obj_info)
            elif obj_type == 3:  # OIFolderInfo
                ks._load_folder_info(data_stream, obj_info)
            elif obj_type == 4:  # OIRouteInfo
                ks._load_route_info(data_stream, obj_info)
            elif obj_type == 5:  # OICameraInfo
                ks._load_camera_info(data_stream, obj_info)
            elif obj_type == 7:  # OITextInfo
                ks._load_text_info(data_stream, obj_info)
            else:
                # Skip unknown object types
                pass
                
            ks.dicObject[key] = obj_info
        
        # Read map info
        ks.map = load_type(data_stream, "i")
        
        # Read caMap (ChangeAmount)
        ks._load_change_amount(data_stream)
        
        # Read sunLightType
        ks.sunLightType = load_type(data_stream, "i")
        
        # Read mapOption
        ks.mapOption = bool(load_type(data_stream, "b"))
        
        # Read aceNo
        ks.aceNo = load_type(data_stream, "i")
        
        # Read aceBlend if version >= 0.0.2
        version_comp = cls._compare_versions(ks.dataVersion, "0.0.2")
        if version_comp >= 0:
            ks.aceBlend = load_type(data_stream, "f")
        
        # Skip some fields for version <= 0.0.1
        if cls._compare_versions(ks.dataVersion, "0.0.1") <= 0:
            load_type(data_stream, "b")  # Skip boolean
            load_type(data_stream, "f")  # Skip float
            load_length(data_stream, "b")  # Skip string
        
        # Read AOE settings if version >= 0.0.2
        if version_comp >= 0:
            ks.enableAOE = bool(load_type(data_stream, "b"))
            ks.aoeColor = cls._parse_color_json(cls._safe_decode(load_length(data_stream, "b")))
            ks.aoeRadius = load_type(data_stream, "f")
        
        # Read bloom settings
        ks.enableBloom = bool(load_type(data_stream, "b"))
        ks.bloomIntensity = load_type(data_stream, "f")
        ks.bloomBlur = load_type(data_stream, "f")
        
        # Read bloomThreshold if version >= 0.0.2
        if version_comp >= 0:
            ks.bloomThreshold = load_type(data_stream, "f")
        
        # Skip boolean for version <= 0.0.1
        if cls._compare_versions(ks.dataVersion, "0.0.1") <= 0:
            load_type(data_stream, "b")
        
        # Read depth settings
        ks.enableDepth = bool(load_type(data_stream, "b"))
        ks.depthFocalSize = load_type(data_stream, "f")
        ks.depthAperture = load_type(data_stream, "f")
        
        # Read vignette settings
        ks.enableVignette = bool(load_type(data_stream, "b"))
        
        # Skip float for version <= 0.0.1
        if cls._compare_versions(ks.dataVersion, "0.0.1") <= 0:
            load_type(data_stream, "f")
        
        # Read fog settings
        ks.enableFog = bool(load_type(data_stream, "b"))
        
        # Read fog color, height, and start distance if version >= 0.0.2
        if version_comp >= 0:
            ks.fogColor = cls._parse_color_json(cls._safe_decode(load_length(data_stream, "b")))
            ks.fogHeight = load_type(data_stream, "f")
            ks.fogStartDistance = load_type(data_stream, "f")
        
        # Read sun shafts settings
        ks.enableSunShafts = bool(load_type(data_stream, "b"))
        
        # Read sun threshold color and sun color if version >= 0.0.2
        if version_comp >= 0:
            ks.sunThresholdColor = cls._parse_color_json(cls._safe_decode(load_length(data_stream, "b")))
            ks.sunColor = cls._parse_color_json(cls._safe_decode(load_length(data_stream, "b")))
        
        # Read sunCaster if version >= 0.0.4
        if cls._compare_versions(ks.dataVersion, "0.0.4") >= 0:
            ks.sunCaster = load_type(data_stream, "i")
        
        # Read enableShadow if version >= 0.0.2
        if version_comp >= 0:
            ks.enableShadow = bool(load_type(data_stream, "b"))
        
        # Read face settings if version >= 0.0.4
        if cls._compare_versions(ks.dataVersion, "0.0.4") >= 0:
            ks.faceNormal = bool(load_type(data_stream, "b"))
            ks.faceShadow = bool(load_type(data_stream, "b"))
            ks.lineColorG = load_type(data_stream, "f")
            ks.ambientShadow = cls._parse_color_json(cls._safe_decode(load_length(data_stream, "b")))
        
        # Read graphic settings if version >= 0.0.5
        try:
            if cls._compare_versions(ks.dataVersion, "0.0.5") >= 0:
                ks.lineWidthG = load_type(data_stream, "f")
                ks.rampG = load_type(data_stream, "i")
                ks.ambientShadowG = load_type(data_stream, "f")
            
            # Read shaderType if version >= 1.1.0.0
            if cls._compare_versions(ks.dataVersion, "1.1.0.0") >= 0:
                ks.shaderType = load_type(data_stream, "i")
            
            # Read skyInfo if version >= 1.1.2.0
            if cls._compare_versions(ks.dataVersion, "1.1.2.0") >= 0:
                sky_info_bytes = load_length(data_stream, "i")
                ks.skyInfo = msg_unpack(sky_info_bytes)
            
            # Read camera data
            ks.cameraSaveData = ks._load_camera_data(data_stream)
            
            # Read camera array data
            ks.cameraData = []
            for i in range(10):
                ks.cameraData.append(ks._load_camera_data(data_stream))
            
            # Read light settings
            ks.charaLight = ks._load_chara_light(data_stream)
            ks.mapLight = ks._load_map_light(data_stream)
            
            # Read BGM, ENV, and outside sound settings
            ks.bgmCtrl = ks._load_bgm_ctrl(data_stream)
            ks.envCtrl = ks._load_env_ctrl(data_stream)
            ks.outsideSoundCtrl = ks._load_outside_sound_ctrl(data_stream)
            
            # Read background and frame
            ks.background = cls._safe_decode(load_length(data_stream, "b"))
            ks.frame = cls._safe_decode(load_length(data_stream, "b"))
        except Exception as e:
            if not safe_mode:
                raise
            print(f"Warning: Error reading scene data: {str(e)}")
            print("Some data may be missing or incorrect.")
        
        return ks
    
    def _load_char_info(self, data_stream, obj_info):
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
            self._skip_bone_info(data_stream)
        
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
            self._skip_ik_target_info(data_stream)
        
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
            self._skip_child_objects(data_stream, child_obj_count)
        
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
        self._skip_look_at_target_info(data_stream)
        
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
        self._skip_voice_ctrl(data_stream)
        
        # Read visible son
        data["visible_son"] = bool(struct.unpack("b", data_stream.read(1))[0])
        
        # Read son length
        data["son_length"] = struct.unpack("f", data_stream.read(4))[0]
        
        # Read visible simple
        data["visible_simple"] = bool(struct.unpack("b", data_stream.read(1))[0])
        
        # Read simple color
        simple_color_json = self._safe_decode(load_length(data_stream, "b"))
        data["simple_color"] = self._parse_color_json(simple_color_json)
        
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
    
    def _load_item_info(self, data_stream, obj_info):
        """Load item info data"""
        # Based on OIItemInfo.Load in C#
        data = {}
        
        # Skip ObjectInfo base data
        self._skip_object_info_base(data_stream)
        
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
            pattern_data = self._load_pattern_info(data_stream)
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
        data["panel"] = self._load_pattern_info(data_stream)
        
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
            self._skip_bone_info(data_stream)
        
        # Read enable dynamic bone
        data["enable_dynamic_bone"] = bool(struct.unpack("b", data_stream.read(1))[0])
        
        # Read anime normalized time
        data["anime_normalized_time"] = struct.unpack("f", data_stream.read(4))[0]
        
        # Read child objects count
        child_count = struct.unpack("i", data_stream.read(4))[0]
        data["child"] = []
        
        # Skip child objects data for now
        # In a real implementation, we would parse the child objects data
        self._skip_child_objects(data_stream, child_count)
        
        obj_info["data"] = data
    
    def _load_light_info(self, data_stream, obj_info):
        """Load light info data"""
        obj_info["data"] = {"type": "light"}
    
    def _load_folder_info(self, data_stream, obj_info):
        """Load folder info data"""
        obj_info["data"] = {"type": "folder"}
    
    def _load_route_info(self, data_stream, obj_info):
        """Load route info data"""
        obj_info["data"] = {"type": "route"}
    
    def _load_camera_info(self, data_stream, obj_info):
        """Load camera info data"""
        obj_info["data"] = {"type": "camera"}
    
    def _load_text_info(self, data_stream, obj_info):
        """Load text info data"""
        obj_info["data"] = {"type": "text"}
    
    def _load_change_amount(self, data_stream):
        """Load ChangeAmount data"""
        # In a complete implementation, we would parse all ChangeAmount data
        # For now, we'll just create a simple structure
        self.caMap = {
            "pos": {"x": 0, "y": 0, "z": 0},
            "rot": {"x": 0, "y": 0, "z": 0},
            "scale": 1.0
        }
    
    def _load_camera_data(self, data_stream):
        """Load camera data"""
        # Simplified implementation
        return {
            "position": {"x": 0, "y": 0, "z": 0},
            "rotation": {"x": 0, "y": 0, "z": 0},
            "distance": 0.0,
            "fieldOfView": 0.0
        }
    
    def _load_chara_light(self, data_stream):
        """Load character light data"""
        # Simplified implementation
        return {
            "color": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
            "shadow": True,
            "intensity": 1.0
        }
    
    def _load_map_light(self, data_stream):
        """Load map light data"""
        # Simplified implementation
        return {
            "color": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
            "shadow": True,
            "intensity": 1.0
        }
    
    def _load_bgm_ctrl(self, data_stream):
        """Load BGM control data"""
        # Simplified implementation
        return {
            "play": False,
            "repeat": 0,
            "no": 0
        }
    
    def _load_env_ctrl(self, data_stream):
        """Load environment control data"""
        # Simplified implementation
        return {
            "play": False,
            "repeat": 0,
            "no": 0
        }
    
    def _load_outside_sound_ctrl(self, data_stream):
        """Load outside sound control data"""
        # Simplified implementation
        return {
            "play": False,
            "repeat": 0,
            "fileName": ""
        }
    
    def _skip_bone_info(self, data_stream):
        """Skip bone info data"""
        # Skip ObjectInfo base data
        self._skip_object_info_base(data_stream)
    
    def _skip_ik_target_info(self, data_stream):
        """Skip IK target info data"""
        # Skip ObjectInfo base data
        self._skip_object_info_base(data_stream)
    
    def _skip_object_info_base(self, data_stream):
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
    
    def _skip_child_objects(self, data_stream, count):
        """Skip child objects data"""
        for _ in range(count):
            # Skip ObjectInfo
            self._skip_object_info_base(data_stream)
    
    def _skip_look_at_target_info(self, data_stream):
        """Skip look at target info data"""
        # Skip ObjectInfo base data
        self._skip_object_info_base(data_stream)
        
        # Skip target type
        data_stream.read(4)  # 1 int
        
        # Skip target number
        data_stream.read(4)  # 1 int
    
    def _skip_voice_ctrl(self, data_stream):
        """Skip voice ctrl data"""
        # Skip play
        data_stream.read(1)  # 1 bool
        
        # Skip repeat
        data_stream.read(4)  # 1 int
        
        # Skip no
        data_stream.read(4)  # 1 int
    
    def _load_pattern_info(self, data_stream):
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
    def _safe_decode(byte_data):
        """Safely decode byte data to string, handling non-UTF-8 encoded data"""
        try:
            return byte_data.decode('utf-8')
        except UnicodeDecodeError:
            try:
                # Try to decode as ASCII, ignoring errors
                return byte_data.decode('ascii', errors='ignore')
            except Exception:
                # If all else fails, return a string representation of the bytes
                return str(byte_data)
    
    @staticmethod
    def _parse_color_json(json_str):
        """Parse color from JSON string"""
        try:
            # Try to parse as JSON
            try:
                color_data = json.loads(json_str)
                return {
                    "r": color_data.get("r", 0),
                    "g": color_data.get("g", 0),
                    "b": color_data.get("b", 0),
                    "a": color_data.get("a", 1.0)
                }
            except json.JSONDecodeError:
                # If the string is not valid JSON, try to extract color values using regex
                import re
                r_match = re.search(r'"r"\s*:\s*([0-9.]+)', json_str)
                g_match = re.search(r'"g"\s*:\s*([0-9.]+)', json_str)
                b_match = re.search(r'"b"\s*:\s*([0-9.]+)', json_str)
                a_match = re.search(r'"a"\s*:\s*([0-9.]+)', json_str)
                
                r = float(r_match.group(1)) if r_match else 1.0
                g = float(g_match.group(1)) if g_match else 1.0
                b = float(b_match.group(1)) if b_match else 1.0
                a = float(a_match.group(1)) if a_match else 1.0
                
                return {"r": r, "g": g, "b": b, "a": a}
        except Exception:
            # If all else fails, return a default color
            print(f"Warning: Could not parse color data: {json_str[:30]}...")
            return {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}
    
    @staticmethod
    def _compare_versions(version1, version2):
        """
        Compare two version strings.
        
        Returns:
            int: -1 if version1 < version2, 0 if version1 == version2, 1 if version1 > version2
        """
        v1_parts = version1.split('.')
        v2_parts = version2.split('.')
        
        # Pad with zeros to make lengths equal
        while len(v1_parts) < len(v2_parts):
            v1_parts.append('0')
        while len(v2_parts) < len(v1_parts):
            v2_parts.append('0')
        
        for i in range(len(v1_parts)):
            v1 = int(v1_parts[i])
            v2 = int(v2_parts[i])
            
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
        
        return 0
    
    def to_dict(self):
        """Convert the scene data to a dictionary"""
        return {
            "version": self.version,
            "dataVersion": self.dataVersion,
            "map": self.map,
            "sunLightType": self.sunLightType,
            "mapOption": self.mapOption,
            "aceNo": self.aceNo,
            "aceBlend": self.aceBlend,
            "enableAOE": self.enableAOE,
            "aoeColor": self.aoeColor,
            "aoeRadius": self.aoeRadius,
            "enableBloom": self.enableBloom,
            "bloomIntensity": self.bloomIntensity,
            "bloomBlur": self.bloomBlur,
            "bloomThreshold": self.bloomThreshold,
            "enableDepth": self.enableDepth,
            "depthFocalSize": self.depthFocalSize,
            "depthAperture": self.depthAperture,
            "enableVignette": self.enableVignette,
            "enableFog": self.enableFog,
            "fogColor": self.fogColor,
            "fogHeight": self.fogHeight,
            "fogStartDistance": self.fogStartDistance,
            "enableSunShafts": self.enableSunShafts,
            "sunThresholdColor": self.sunThresholdColor,
            "sunColor": self.sunColor,
            "sunCaster": self.sunCaster,
            "enableShadow": self.enableShadow,
            "faceNormal": self.faceNormal,
            "faceShadow": self.faceShadow,
            "lineColorG": self.lineColorG,
            "ambientShadow": self.ambientShadow,
            "lineWidthG": self.lineWidthG,
            "rampG": self.rampG,
            "ambientShadowG": self.ambientShadowG,
            "shaderType": self.shaderType,
            "skyInfo": self.skyInfo,
            "background": self.background,
            "frame": self.frame,
            "objectCount": len(self.dicObject)
        }
    
    def __str__(self):
        """String representation of the scene data"""
        return f"KoikatuSceneData(version={self.version}, objects={len(self.dicObject)})"
