# -*- coding:utf-8 -*-

import io
import json
import struct
from typing import Union

from kkloader.funcs import get_png, load_length, load_string, load_type, msg_unpack, msg_pack, write_string
from kkloader.KoikatuSceneObjectLoader import KoikatuSceneObjectLoader


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

        ks.image = get_png(data_stream)
        version_str = load_length(data_stream, "b").decode('utf-8')

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
            
            # Load object data based on type
            if obj_type == 0:  # OICharInfo
                KoikatuSceneObjectLoader.load_char_info(data_stream, obj_info)
            elif obj_type == 1:  # OIItemInfo
                KoikatuSceneObjectLoader.load_item_info(data_stream, obj_info)
            elif obj_type == 2:  # OILightInfo
                KoikatuSceneObjectLoader.load_light_info(data_stream, obj_info)
            elif obj_type == 3:  # OIFolderInfo
                KoikatuSceneObjectLoader.load_folder_info(data_stream, obj_info)
            elif obj_type == 4:  # OIRouteInfo
                KoikatuSceneObjectLoader.load_route_info(data_stream, obj_info)
            elif obj_type == 5:  # OICameraInfo
                KoikatuSceneObjectLoader.load_camera_info(data_stream, obj_info)
            elif obj_type == 7:  # OITextInfo
                KoikatuSceneObjectLoader.load_text_info(data_stream, obj_info)
            else:
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
            ks.aoeColor = cls._parse_color_json(load_length(data_stream, "b").decode('utf-8'))
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
            ks.fogColor = cls._parse_color_json(load_length(data_stream, "b").decode('utf-8'))
            ks.fogHeight = load_type(data_stream, "f")
            ks.fogStartDistance = load_type(data_stream, "f")
        
        # Read sun shafts settings
        ks.enableSunShafts = bool(load_type(data_stream, "b"))
        
        # Read sun threshold color and sun color if version >= 0.0.2
        if version_comp >= 0:
            ks.sunThresholdColor = cls._parse_color_json(load_length(data_stream, "b").decode('utf-8'))
            ks.sunColor = cls._parse_color_json(load_length(data_stream, "b").decode('utf-8'))
        
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
            ks.ambientShadow = cls._parse_color_json(load_length(data_stream, "b").decode('utf-8'))

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
        ks.background = load_length(data_stream, "b").decode('utf-8')
        ks.frame = load_length(data_stream, "b").decode('utf-8')
        
        return ks
    
    
    def _load_change_amount(self, data_stream):
        """
        Load ChangeAmount data
        Based on ChangeAmount.Load in C#
        """
        # Read position (Vector3)
        pos_x = load_type(data_stream, "f")
        pos_y = load_type(data_stream, "f")
        pos_z = load_type(data_stream, "f")
        
        # Read rotation (Vector3)
        rot_x = load_type(data_stream, "f")
        rot_y = load_type(data_stream, "f")
        rot_z = load_type(data_stream, "f")
        
        # Read scale (Vector3)
        scale_x = load_type(data_stream, "f")
        scale_y = load_type(data_stream, "f")
        scale_z = load_type(data_stream, "f")
        
        self.caMap = {
            "pos": {"x": pos_x, "y": pos_y, "z": pos_z},
            "rot": {"x": rot_x, "y": rot_y, "z": rot_z},
            "scale": {"x": scale_x, "y": scale_y, "z": scale_z}
        }
    
    def _load_camera_data(self, data_stream):
        """
        Load camera data
        Based on CameraControl.CameraData.Load in C#
        """
        # Read version
        version = load_type(data_stream, "i")
        # Read position (Vector3)
        pos_x = load_type(data_stream, "f")
        pos_y = load_type(data_stream, "f")
        pos_z = load_type(data_stream, "f")
        
        # Read rotation (Vector3)
        rot_x = load_type(data_stream, "f")
        rot_y = load_type(data_stream, "f")
        rot_z = load_type(data_stream, "f")
        
        # Read distance (Vector3) or skip based on version
        if version == 1:
            # In version 1, only read a single float
            load_type(data_stream, "f")  # Skip this value
            distance_x = 0.0
            distance_y = 0.0
            distance_z = 0.0
        else:
            # In version 2+, read three floats
            distance_x = load_type(data_stream, "f")
            distance_y = load_type(data_stream, "f")
            distance_z = load_type(data_stream, "f")
        
        # Read field of view (parse)
        field_of_view = load_type(data_stream, "f")
        
        return {
            "position": {"x": pos_x, "y": pos_y, "z": pos_z},
            "rotation": {"x": rot_x, "y": rot_y, "z": rot_z},
            "distance": {"x": distance_x, "y": distance_y, "z": distance_z},
            "fieldOfView": field_of_view
        }
    
    def _load_chara_light(self, data_stream):
        """
        Load character light data
        Based on CameraLightCtrl.LightInfo.Load in C#
        """
        # Read color (JSON string)
        color_json = load_string(data_stream).decode('utf-8')
        color = self._parse_color_json(color_json)
        
        # Read intensity (float)
        intensity = load_type(data_stream, "f")
        
        # Read rotation (2 floats)
        rot = [
            load_type(data_stream, "f"),
            load_type(data_stream, "f")
        ]
        
        # Read shadow (boolean)
        shadow = bool(load_type(data_stream, "b"))
        
        return {
            "color": color,
            "intensity": intensity,
            "rot": rot,
            "shadow": shadow
        }
    
    def _load_map_light(self, data_stream):
        """
        Load map light data
        Based on CameraLightCtrl.MapLightInfo.Load in C#
        """
        # First load base LightInfo data
        # Read color (JSON string)
        color_json = load_string(data_stream).decode('utf-8')
        color = self._parse_color_json(color_json)
        
        # Read intensity (float)
        intensity = load_type(data_stream, "f")
        
        # Read rotation (2 floats)
        rot = [
            load_type(data_stream, "f"),
            load_type(data_stream, "f")
        ]
        
        # Read shadow (boolean)
        shadow = bool(load_type(data_stream, "b"))
        
        # Read MapLightInfo specific data
        # Read light type (int)
        light_type = load_type(data_stream, "i")
        
        return {
            "color": color,
            "intensity": intensity,
            "rot": rot,
            "shadow": shadow,
            "type": light_type
        }
    
    def _load_bgm_ctrl(self, data_stream):
        """
        Load BGM control data
        Based on BGMCtrl.Load in C#
        """
        # Read repeat mode (int32)
        repeat = load_type(data_stream, "i")
        
        # Read BGM number (int32)
        no = load_type(data_stream, "i")
        
        # Read play state (boolean)
        play = bool(load_type(data_stream, "b"))
        
        return {
            "play": play,
            "repeat": repeat,
            "no": no
        }
    
    def _load_env_ctrl(self, data_stream):
        """
        Load environment control data
        Based on ENVCtrl.Load in C#
        """
        # Read repeat mode (int32)
        repeat = load_type(data_stream, "i")
        
        # Read ENV number (int32)
        no = load_type(data_stream, "i")
        
        # Read play state (boolean)
        play = bool(load_type(data_stream, "b"))
        
        return {
            "play": play,
            "repeat": repeat,
            "no": no
        }
    
    def _load_outside_sound_ctrl(self, data_stream):
        """
        Load outside sound control data
        Based on OutsideSoundCtrl.Load in C#
        """
        # Read repeat mode (int32)
        repeat = load_type(data_stream, "i")
        
        # Read file name (string)
        file_name = load_string(data_stream).decode('utf-8')
        
        # Read play state (boolean)
        play = bool(load_type(data_stream, "b"))
        
        return {
            "play": play,
            "repeat": repeat,
            "fileName": file_name
        }
    
    
    @staticmethod
    def _parse_color_json(json_str):
        """Parse color from JSON string"""
        return KoikatuSceneObjectLoader.parse_color_json(json_str)
    
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
    
    def save(self, filelike: Union[str, io.BytesIO]) -> None:
        """
        Save Koikatu scene data to a file or BytesIO object.
        
        Args:
            filelike: Path to the file or BytesIO object to save the scene data to
        """
        if isinstance(filelike, str):
            with open(filelike, "bw") as f:
                f.write(bytes(self))
        elif isinstance(filelike, io.BytesIO):
            filelike.write(bytes(self))
        else:
            raise ValueError(f"Unsupported output type: {type(filelike)}")
    
    def __bytes__(self) -> bytes:
        """
        Convert the scene data to bytes.
        
        Returns:
            bytes: The scene data as bytes
        """
        data_stream = io.BytesIO()
        
        # Write PNG data if available
        if self.image:
            data_stream.write(self.image)
        
        # Write version
        version_bytes = self.version.encode('utf-8')
        data_stream.write(struct.pack("b", len(version_bytes)))
        data_stream.write(version_bytes)
        
        # Write object dictionary
        data_stream.write(struct.pack("i", len(self.dicObject)))
        for key, obj_info in self.dicObject.items():
            data_stream.write(struct.pack("i", key))
            data_stream.write(struct.pack("i", obj_info["type"]))
            
            # Save object data based on type
            try:
                if obj_info["type"] == 0:  # OICharInfo
                    KoikatuSceneObjectLoader.save_char_info(data_stream, obj_info)
                elif obj_info["type"] == 1:  # OIItemInfo
                    KoikatuSceneObjectLoader.save_item_info(data_stream, obj_info)
                elif obj_info["type"] == 2:  # OILightInfo
                    KoikatuSceneObjectLoader.save_light_info(data_stream, obj_info)
                elif obj_info["type"] == 3:  # OIFolderInfo
                    KoikatuSceneObjectLoader.save_folder_info(data_stream, obj_info)
                elif obj_info["type"] == 4:  # OIRouteInfo
                    KoikatuSceneObjectLoader.save_route_info(data_stream, obj_info)
                elif obj_info["type"] == 5:  # OICameraInfo
                    KoikatuSceneObjectLoader.save_camera_info(data_stream, obj_info)
                elif obj_info["type"] == 7:  # OITextInfo
                    KoikatuSceneObjectLoader.save_text_info(data_stream, obj_info)
                else:
                    raise ValueError(f"Unknown object type:{obj_info['type']}")
            except NotImplementedError as e:
                # 実装されていない関数が呼ばれた場合は、エラーを発生させる
                raise NotImplementedError(f"Cannot save object of type {obj_info['type']}: {str(e)}")
        
        # Write map info
        data_stream.write(struct.pack("i", self.map))
        
        # Write caMap (ChangeAmount)
        self._save_change_amount(data_stream)
        
        # Write sunLightType
        data_stream.write(struct.pack("i", self.sunLightType))
        
        # Write mapOption
        data_stream.write(struct.pack("b", int(self.mapOption)))
        
        # Write aceNo
        data_stream.write(struct.pack("i", self.aceNo))
        
        # Write aceBlend
        data_stream.write(struct.pack("f", self.aceBlend))
        
        # Write AOE settings
        data_stream.write(struct.pack("b", int(self.enableAOE)))
        aoe_color_bytes = json.dumps(self.aoeColor).encode('utf-8')
        data_stream.write(struct.pack("b", len(aoe_color_bytes)))
        data_stream.write(aoe_color_bytes)
        data_stream.write(struct.pack("f", self.aoeRadius))
        
        # Write bloom settings
        data_stream.write(struct.pack("b", int(self.enableBloom)))
        data_stream.write(struct.pack("f", self.bloomIntensity))
        data_stream.write(struct.pack("f", self.bloomBlur))
        data_stream.write(struct.pack("f", self.bloomThreshold))
        
        # Write depth settings
        data_stream.write(struct.pack("b", int(self.enableDepth)))
        data_stream.write(struct.pack("f", self.depthFocalSize))
        data_stream.write(struct.pack("f", self.depthAperture))
        
        # Write vignette settings
        data_stream.write(struct.pack("b", int(self.enableVignette)))
        
        # Write fog settings
        data_stream.write(struct.pack("b", int(self.enableFog)))
        fog_color_bytes = json.dumps(self.fogColor).encode('utf-8')
        data_stream.write(struct.pack("b", len(fog_color_bytes)))
        data_stream.write(fog_color_bytes)
        data_stream.write(struct.pack("f", self.fogHeight))
        data_stream.write(struct.pack("f", self.fogStartDistance))
        
        # Write sun shafts settings
        data_stream.write(struct.pack("b", int(self.enableSunShafts)))
        sun_threshold_color_bytes = json.dumps(self.sunThresholdColor).encode('utf-8')
        data_stream.write(struct.pack("b", len(sun_threshold_color_bytes)))
        data_stream.write(sun_threshold_color_bytes)
        sun_color_bytes = json.dumps(self.sunColor).encode('utf-8')
        data_stream.write(struct.pack("b", len(sun_color_bytes)))
        data_stream.write(sun_color_bytes)
        
        # Write sunCaster
        data_stream.write(struct.pack("i", self.sunCaster))
        
        # Write enableShadow
        data_stream.write(struct.pack("b", int(self.enableShadow)))
        
        # Write face settings
        data_stream.write(struct.pack("b", int(self.faceNormal)))
        data_stream.write(struct.pack("b", int(self.faceShadow)))
        data_stream.write(struct.pack("f", self.lineColorG))
        ambient_shadow_bytes = json.dumps(self.ambientShadow).encode('utf-8')
        data_stream.write(struct.pack("b", len(ambient_shadow_bytes)))
        data_stream.write(ambient_shadow_bytes)
        
        # Write additional face settings
        data_stream.write(struct.pack("f", self.lineWidthG))
        data_stream.write(struct.pack("i", self.rampG))
        data_stream.write(struct.pack("f", self.ambientShadowG))
        
        # Write shaderType
        data_stream.write(struct.pack("i", self.shaderType))
        
        # Write skyInfo
        sky_info_bytes, sky_info_len = msg_pack(self.skyInfo)
        data_stream.write(struct.pack("i", sky_info_len))
        data_stream.write(sky_info_bytes)
        
        # Write camera data
        self._save_camera_data(data_stream, self.cameraSaveData)
        
        # Write camera array data
        for camera in self.cameraData:
            self._save_camera_data(data_stream, camera)
        
        # Write light settings
        self._save_chara_light(data_stream, self.charaLight)
        self._save_map_light(data_stream, self.mapLight)
        
        # Write BGM, ENV, and outside sound settings
        self._save_bgm_ctrl(data_stream, self.bgmCtrl)
        self._save_env_ctrl(data_stream, self.envCtrl)
        self._save_outside_sound_ctrl(data_stream, self.outsideSoundCtrl)
        
        # Write background and frame
        background_bytes = self.background.encode('utf-8')
        data_stream.write(struct.pack("b", len(background_bytes)))
        data_stream.write(background_bytes)
        frame_bytes = self.frame.encode('utf-8')
        data_stream.write(struct.pack("b", len(frame_bytes)))
        data_stream.write(frame_bytes)
        
        return data_stream.getvalue()
    
    def _save_change_amount(self, data_stream):
        """
        Save ChangeAmount data
        Based on ChangeAmount.Save in C#
        """
        # Write position (Vector3)
        data_stream.write(struct.pack("f", self.caMap["pos"]["x"]))
        data_stream.write(struct.pack("f", self.caMap["pos"]["y"]))
        data_stream.write(struct.pack("f", self.caMap["pos"]["z"]))
        
        # Write rotation (Vector3)
        data_stream.write(struct.pack("f", self.caMap["rot"]["x"]))
        data_stream.write(struct.pack("f", self.caMap["rot"]["y"]))
        data_stream.write(struct.pack("f", self.caMap["rot"]["z"]))
        
        # Write scale (Vector3)
        data_stream.write(struct.pack("f", self.caMap["scale"]["x"]))
        data_stream.write(struct.pack("f", self.caMap["scale"]["y"]))
        data_stream.write(struct.pack("f", self.caMap["scale"]["z"]))
    
    def _save_camera_data(self, data_stream, camera_data):
        """
        Save camera data
        Based on CameraControl.CameraData.Save in C#
        """
        
        # Write version (always use version 2)
        data_stream.write(struct.pack("i", 2))
        
        # Write position (Vector3)
        data_stream.write(struct.pack("f", camera_data["position"]["x"]))
        data_stream.write(struct.pack("f", camera_data["position"]["y"]))
        data_stream.write(struct.pack("f", camera_data["position"]["z"]))
        
        # Write rotation (Vector3)
        data_stream.write(struct.pack("f", camera_data["rotation"]["x"]))
        data_stream.write(struct.pack("f", camera_data["rotation"]["y"]))
        data_stream.write(struct.pack("f", camera_data["rotation"]["z"]))
        
        # Write distance (Vector3)
        data_stream.write(struct.pack("f", camera_data["distance"]["x"]))
        data_stream.write(struct.pack("f", camera_data["distance"]["y"]))
        data_stream.write(struct.pack("f", camera_data["distance"]["z"]))
        
        # Write field of view
        data_stream.write(struct.pack("f", camera_data["fieldOfView"]))
        
    
    def _save_chara_light(self, data_stream, light_data):
        """
        Save character light data
        Based on CameraLightCtrl.LightInfo.Save in C#
        """
        
        # Write color (JSON string)
        color_bytes = json.dumps(light_data["color"]).encode('utf-8')
        self._write_string(data_stream, color_bytes)
        
        # Write intensity (float)
        data_stream.write(struct.pack("f", light_data["intensity"]))
        
        # Write rotation (2 floats)
        data_stream.write(struct.pack("f", light_data["rot"][0]))
        data_stream.write(struct.pack("f", light_data["rot"][1]))
        
        # Write shadow (boolean)
        data_stream.write(struct.pack("b", int(light_data["shadow"])))
        
    
    def _save_map_light(self, data_stream, light_data):
        """
        Save map light data
        Based on CameraLightCtrl.MapLightInfo.Save in C#
        """
        
        # First save base LightInfo data
        # Write color (JSON string)
        color_bytes = json.dumps(light_data["color"]).encode('utf-8')
        self._write_string(data_stream, color_bytes)
        
        # Write intensity (float)
        data_stream.write(struct.pack("f", light_data["intensity"]))
        
        # Write rotation (2 floats)
        data_stream.write(struct.pack("f", light_data["rot"][0]))
        data_stream.write(struct.pack("f", light_data["rot"][1]))
        
        # Write shadow (boolean)
        data_stream.write(struct.pack("b", int(light_data["shadow"])))
        
        # Write MapLightInfo specific data
        # Write light type (int)
        data_stream.write(struct.pack("i", light_data["type"]))
        
    
    def _save_bgm_ctrl(self, data_stream, bgm_data):
        """
        Save BGM control data
        Based on BGMCtrl.Save in C#
        """
        # Write repeat mode (int32)
        data_stream.write(struct.pack("i", bgm_data["repeat"]))
        
        # Write BGM number (int32)
        data_stream.write(struct.pack("i", bgm_data["no"]))
        
        # Write play state (boolean)
        data_stream.write(struct.pack("b", int(bgm_data["play"])))
    
    def _save_env_ctrl(self, data_stream, env_data):
        """
        Save environment control data
        Based on ENVCtrl.Save in C#
        """
        # Write repeat mode (int32)
        data_stream.write(struct.pack("i", env_data["repeat"]))
        
        # Write ENV number (int32)
        data_stream.write(struct.pack("i", env_data["no"]))
        
        # Write play state (boolean)
        data_stream.write(struct.pack("b", int(env_data["play"])))
    
    def _save_outside_sound_ctrl(self, data_stream, sound_data):
        """
        Save outside sound control data
        Based on OutsideSoundCtrl.Save in C#
        """
        # Write repeat mode (int32)
        data_stream.write(struct.pack("i", sound_data["repeat"]))
        
        # Write file name (string)
        file_name_bytes = sound_data["fileName"].encode('utf-8')
        self._write_string(data_stream, file_name_bytes)
        
        # Write play state (boolean)
        data_stream.write(struct.pack("b", int(sound_data["play"])))
    
    def _write_string(self, data_stream, value):
        """
        Write a string to the data stream using the same format as load_string
        Using write_string from funcs.py
        """
        write_string(data_stream, value)
    
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
