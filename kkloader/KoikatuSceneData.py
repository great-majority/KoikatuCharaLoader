import io
import json
import struct
from typing import Union

from kkloader.funcs import get_png, load_length, load_string, load_type, msg_pack, msg_unpack, write_string
from kkloader.KoikatuSceneObjectLoader import KoikatuSceneObjectLoader


class KoikatuSceneData:
    """
    Class for loading and parsing Koikatu scene data.
    This is a Python implementation of the Studio.SceneInfo.Load function in C#.
    """

    # ============================================================
    # 1. INITIALIZATION & CLASS METHODS
    # ============================================================
    """
    Core initialization and loading methods.

    - __init__: Initialize scene data with default values for all fields
    - load: Class method to load scene data from files, bytes, or BytesIO objects

    The load method handles version-aware deserialization, supporting multiple
    scene file format versions (0.0.1 through 1.1.2.1+).
    """

    def __init__(self):
        self.image = None
        self.version = None
        self.dataVersion = None
        self.objects = {}
        self.map = -1
        self.caMap = {}
        self.sunLightType = 0
        self.mapOption = True
        self.aceNo = 0
        self.aceBlend = 0.0
        self.enableAOE = True
        self.aoeColor = {"r": 180 / 255, "g": 180 / 255, "b": 180 / 255, "a": 1.0}
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
        self.fogColor = {"r": 137 / 255, "g": 193 / 255, "b": 221 / 255, "a": 1.0}
        self.fogHeight = 1.0
        self.fogStartDistance = 0.0
        self.enableSunShafts = False
        self.sunThresholdColor = {"r": 128 / 255, "g": 128 / 255, "b": 128 / 255, "a": 1.0}
        self.sunColor = {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}
        self.sunCaster = -1
        self.enableShadow = True
        self.faceNormal = False
        self.faceShadow = False
        self.lineColorG = 0.0
        self.ambientShadow = {"r": 128 / 255, "g": 128 / 255, "b": 128 / 255, "a": 1.0}
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
    def load(cls, filelike: Union[str, bytes, io.BytesIO]) -> "KoikatuSceneData":
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
        version_str = load_string(data_stream).decode("utf-8")

        ks.version = version_str
        ks.dataVersion = version_str

        # Read object dictionary
        obj_count = load_type(data_stream, "i")
        for _ in range(obj_count):
            key = load_type(data_stream, "i")
            obj_type = load_type(data_stream, "i")

            # Create object info based on type
            obj_info = {"type": obj_type, "data": {}}

            # Load object data based on type
            KoikatuSceneObjectLoader._dispatch_load(data_stream, obj_type, obj_info, version_str)

            ks.objects[key] = obj_info

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

        # Read deprecated fields for version <= 0.0.1
        if cls._compare_versions(ks.dataVersion, "0.0.1") <= 0:
            ks.deprecated_v001_bool = bool(load_type(data_stream, "b"))
            ks.deprecated_v001_float = load_type(data_stream, "f")
            ks.deprecated_v001_string = load_length(data_stream, "b").decode("utf-8")

        # Read AOE settings if version >= 0.0.2
        if version_comp >= 0:
            ks.enableAOE = bool(load_type(data_stream, "b"))
            ks.aoeColor = cls._parse_color_json(load_length(data_stream, "b").decode("utf-8"))
            ks.aoeRadius = load_type(data_stream, "f")

        # Read bloom settings
        ks.enableBloom = bool(load_type(data_stream, "b"))
        ks.bloomIntensity = load_type(data_stream, "f")
        ks.bloomBlur = load_type(data_stream, "f")

        # Read bloomThreshold if version >= 0.0.2
        if version_comp >= 0:
            ks.bloomThreshold = load_type(data_stream, "f")

        # Read deprecated boolean for version <= 0.0.1
        if cls._compare_versions(ks.dataVersion, "0.0.1") <= 0:
            ks.deprecated_v001_bool2 = bool(load_type(data_stream, "b"))

        # Read depth settings
        ks.enableDepth = bool(load_type(data_stream, "b"))
        ks.depthFocalSize = load_type(data_stream, "f")
        ks.depthAperture = load_type(data_stream, "f")

        # Read vignette settings
        ks.enableVignette = bool(load_type(data_stream, "b"))

        # Read deprecated float for version <= 0.0.1
        if cls._compare_versions(ks.dataVersion, "0.0.1") <= 0:
            ks.deprecated_v001_float2 = load_type(data_stream, "f")

        # Read fog settings
        ks.enableFog = bool(load_type(data_stream, "b"))

        # Read fog color, height, and start distance if version >= 0.0.2
        if version_comp >= 0:
            ks.fogColor = cls._parse_color_json(load_length(data_stream, "b").decode("utf-8"))
            ks.fogHeight = load_type(data_stream, "f")
            ks.fogStartDistance = load_type(data_stream, "f")

        # Read sun shafts settings
        ks.enableSunShafts = bool(load_type(data_stream, "b"))

        # Read sun threshold color and sun color if version >= 0.0.2
        if version_comp >= 0:
            ks.sunThresholdColor = cls._parse_color_json(load_length(data_stream, "b").decode("utf-8"))
            ks.sunColor = cls._parse_color_json(load_length(data_stream, "b").decode("utf-8"))

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
            ks.ambientShadow = cls._parse_color_json(load_length(data_stream, "b").decode("utf-8"))

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
        for _ in range(10):
            ks.cameraData.append(ks._load_camera_data(data_stream))

        # Read light settings
        ks.charaLight = ks._load_chara_light(data_stream)
        ks.mapLight = ks._load_map_light(data_stream)

        # Read BGM, ENV, and outside sound settings
        ks.bgmCtrl = ks._load_bgm_ctrl(data_stream)
        ks.envCtrl = ks._load_env_ctrl(data_stream)
        ks.outsideSoundCtrl = ks._load_outside_sound_ctrl(data_stream)

        # Read background and frame
        ks.background = load_length(data_stream, "b").decode("utf-8")
        ks.frame = load_length(data_stream, "b").decode("utf-8")

        # 【KStudio】
        ks.tail = load_string(data_stream).decode("utf-8")
        assert ks.tail == "【KStudio】"

        # Mod-related data follows.
        mods_data = data_stream.read()
        if len(mods_data) != 0:
            mod_data_stream = io.BytesIO(mods_data)
            ks.mod_header = load_length(mod_data_stream, "b").decode("utf-8")
            ks.mod_unknown = load_type(mod_data_stream, "i")  # 3
            ks.mod_data = msg_unpack(load_length(mod_data_stream, "i"))
            ks.mod_tail = mod_data_stream.read()  # this is usually empty.

        return ks

    # ============================================================
    # 2. PUBLIC INTERFACE METHODS
    # ============================================================
    """
    Public API for interacting with scene data.

    - save: Save scene data to file or BytesIO
    - __bytes__: Convert scene to binary bytes (used by save)
    - to_dict: Convert scene metadata to dictionary
    - __str__: String representation for debugging

    These methods provide the main user-facing interface for working with scenes.
    """

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

        # Write version (always save with latest version like C# does with m_Version = 1.1.2.1)
        save_version = "1.1.2.1"
        version_bytes = save_version.encode("utf-8")
        data_stream.write(struct.pack("b", len(version_bytes)))
        data_stream.write(version_bytes)

        # Write object dictionary
        data_stream.write(struct.pack("i", len(self.objects)))
        for key, obj_info in self.objects.items():
            data_stream.write(struct.pack("i", key))
            data_stream.write(struct.pack("i", obj_info["type"]))

            # Save object data based on type (using save_version, not self.version)
            try:
                KoikatuSceneObjectLoader._dispatch_save(data_stream, obj_info, save_version)
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
        aoe_color_bytes = json.dumps(self.aoeColor, separators=(",", ":")).encode("utf-8")
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
        fog_color_bytes = json.dumps(self.fogColor, separators=(",", ":")).encode("utf-8")
        data_stream.write(struct.pack("b", len(fog_color_bytes)))
        data_stream.write(fog_color_bytes)
        data_stream.write(struct.pack("f", self.fogHeight))
        data_stream.write(struct.pack("f", self.fogStartDistance))

        # Write sun shafts settings
        data_stream.write(struct.pack("b", int(self.enableSunShafts)))
        sun_threshold_color_bytes = json.dumps(self.sunThresholdColor, separators=(",", ":")).encode("utf-8")
        data_stream.write(struct.pack("b", len(sun_threshold_color_bytes)))
        data_stream.write(sun_threshold_color_bytes)
        sun_color_bytes = json.dumps(self.sunColor, separators=(",", ":")).encode("utf-8")
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
        ambient_shadow_bytes = json.dumps(self.ambientShadow, separators=(",", ":")).encode("utf-8")
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
        background_bytes = self.background.encode("utf-8")
        data_stream.write(struct.pack("b", len(background_bytes)))
        data_stream.write(background_bytes)
        frame_bytes = self.frame.encode("utf-8")
        data_stream.write(struct.pack("b", len(frame_bytes)))
        data_stream.write(frame_bytes)

        tail_bytes = self.tail.encode("utf-8")
        data_stream.write(struct.pack("b", len(tail_bytes)))
        data_stream.write(tail_bytes)

        # Write mod-related data if present
        if hasattr(self, "mod_header") and self.mod_header:
            mod_header_bytes = self.mod_header.encode("utf-8")
            data_stream.write(struct.pack("b", len(mod_header_bytes)))
            data_stream.write(mod_header_bytes)
            data_stream.write(struct.pack("i", self.mod_unknown))
            mod_data_bytes, mod_data_len = msg_pack(self.mod_data)
            data_stream.write(struct.pack("i", mod_data_len))
            data_stream.write(mod_data_bytes)
            if hasattr(self, "mod_tail") and self.mod_tail:
                data_stream.write(self.mod_tail)

        return data_stream.getvalue()

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
            "objectCount": len(self.objects),
        }

    def __str__(self):
        """String representation of the scene data"""
        return f"KoikatuSceneData(version={self.version}, objects={len(self.objects)})"

    # ============================================================
    # 3. PRIMITIVE TYPE HELPERS
    # ============================================================
    """
    Low-level data type helpers.

    - _load_vector3_as_tuple: Read Vector3 as tuple (x, y, z)
    - _save_vector3_dict: Write Vector3 from dictionary {x, y, z}

    These methods handle basic 3D vector serialization used throughout the scene format.
    """

    @staticmethod
    def _load_vector3_as_tuple(data_stream):
        """Load a Vector3 (x, y, z) from the data stream and return as tuple of floats"""
        return (load_type(data_stream, "f"), load_type(data_stream, "f"), load_type(data_stream, "f"))

    @staticmethod
    def _save_vector3_dict(data_stream, vector3_dict):
        """Save a Vector3 dictionary (x, y, z) to the data stream"""
        data_stream.write(struct.pack("f", vector3_dict["x"]))
        data_stream.write(struct.pack("f", vector3_dict["y"]))
        data_stream.write(struct.pack("f", vector3_dict["z"]))

    # ============================================================
    # 4. SCENE DATA COMPONENT LOADERS
    # ============================================================
    """
    Scene-level component load methods.

    These methods handle loading various scene-wide settings:
    - _load_change_amount: Map transform data (position, rotation, scale)
    - _load_camera_data: Camera position, rotation, FOV settings
    - _load_chara_light: Character lighting configuration
    - _load_map_light: Map/environment lighting configuration
    - _load_bgm_ctrl: Background music control settings
    - _load_env_ctrl: Environment sound control settings
    - _load_outside_sound_ctrl: Outdoor ambient sound settings

    All methods correspond to C# serialization classes in Studio.
    """

    def _load_change_amount(self, data_stream):
        """
        Load ChangeAmount data
        Based on ChangeAmount.Load in C#
        """
        # Read position (Vector3)
        pos_x, pos_y, pos_z = self._load_vector3_as_tuple(data_stream)

        # Read rotation (Vector3)
        rot_x, rot_y, rot_z = self._load_vector3_as_tuple(data_stream)

        # Read scale (Vector3)
        scale_x, scale_y, scale_z = self._load_vector3_as_tuple(data_stream)

        self.caMap = {"pos": {"x": pos_x, "y": pos_y, "z": pos_z}, "rot": {"x": rot_x, "y": rot_y, "z": rot_z}, "scale": {"x": scale_x, "y": scale_y, "z": scale_z}}

    def _load_camera_data(self, data_stream):
        """
        Load camera data
        Based on CameraControl.CameraData.Load in C#
        """
        # Read version
        version = load_type(data_stream, "i")

        # Read position (Vector3)
        pos_x, pos_y, pos_z = self._load_vector3_as_tuple(data_stream)

        # Read rotation (Vector3)
        rot_x, rot_y, rot_z = self._load_vector3_as_tuple(data_stream)

        # Read distance (Vector3) based on version
        if version == 1:
            # In version 1, only a single float exists (deprecated field)
            deprecated_distance = load_type(data_stream, "f")
            distance_x = 0.0
            distance_y = 0.0
            distance_z = 0.0
        else:
            # In version 2+, read three floats
            deprecated_distance = None
            distance_x, distance_y, distance_z = self._load_vector3_as_tuple(data_stream)

        # Read field of view (parse)
        field_of_view = load_type(data_stream, "f")

        result = {"position": {"x": pos_x, "y": pos_y, "z": pos_z}, "rotation": {"x": rot_x, "y": rot_y, "z": rot_z}, "distance": {"x": distance_x, "y": distance_y, "z": distance_z}, "fieldOfView": field_of_view}
        if deprecated_distance is not None:
            result["deprecated_distance"] = deprecated_distance
        return result

    def _load_chara_light(self, data_stream):
        """
        Load character light data
        Based on CameraLightCtrl.LightInfo.Load in C#
        """
        return KoikatuSceneObjectLoader._load_light_info_base(data_stream)

    def _load_map_light(self, data_stream):
        """
        Load map light data
        Based on CameraLightCtrl.MapLightInfo.Load in C#
        """
        # First load base LightInfo data
        result = KoikatuSceneObjectLoader._load_light_info_base(data_stream)

        # Read MapLightInfo specific data
        # Read light type (int)
        result["type"] = load_type(data_stream, "i")

        return result

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

        return {"play": play, "repeat": repeat, "no": no}

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

        return {"play": play, "repeat": repeat, "no": no}

    def _load_outside_sound_ctrl(self, data_stream):
        """
        Load outside sound control data
        Based on OutsideSoundCtrl.Load in C#
        """
        # Read repeat mode (int32)
        repeat = load_type(data_stream, "i")

        # Read file name (string)
        file_name = load_string(data_stream).decode("utf-8")

        # Read play state (boolean)
        play = bool(load_type(data_stream, "b"))

        return {"play": play, "repeat": repeat, "fileName": file_name}

    # ============================================================
    # 5. SCENE DATA COMPONENT SAVERS
    # ============================================================
    """
    Scene-level component save methods.

    These methods handle saving various scene-wide settings:
    - _save_change_amount: Map transform data (position, rotation, scale)
    - _save_camera_data: Camera position, rotation, FOV settings
    - _save_chara_light: Character lighting configuration
    - _save_map_light: Map/environment lighting configuration
    - _save_bgm_ctrl: Background music control settings
    - _save_env_ctrl: Environment sound control settings
    - _save_outside_sound_ctrl: Outdoor ambient sound settings

    All methods correspond to C# serialization classes in Studio.
    """

    def _save_change_amount(self, data_stream):
        """
        Save ChangeAmount data
        Based on ChangeAmount.Save in C#
        """
        # Write position (Vector3)
        self._save_vector3_dict(data_stream, self.caMap["pos"])

        # Write rotation (Vector3)
        self._save_vector3_dict(data_stream, self.caMap["rot"])

        # Write scale (Vector3)
        self._save_vector3_dict(data_stream, self.caMap["scale"])

    def _save_camera_data(self, data_stream, camera_data):
        """
        Save camera data
        Based on CameraControl.CameraData.Save in C#
        """

        # Write version (always use version 2)
        data_stream.write(struct.pack("i", 2))

        # Write position (Vector3)
        self._save_vector3_dict(data_stream, camera_data["position"])

        # Write rotation (Vector3)
        self._save_vector3_dict(data_stream, camera_data["rotation"])

        # Write distance (Vector3)
        self._save_vector3_dict(data_stream, camera_data["distance"])

        # Write field of view
        data_stream.write(struct.pack("f", camera_data["fieldOfView"]))

    def _save_chara_light(self, data_stream, light_data):
        """
        Save character light data
        Based on CameraLightCtrl.LightInfo.Save in C#
        """
        KoikatuSceneObjectLoader._save_light_info_base(data_stream, light_data)

    def _save_map_light(self, data_stream, light_data):
        """
        Save map light data
        Based on CameraLightCtrl.MapLightInfo.Save in C#
        """
        # First save base LightInfo data
        KoikatuSceneObjectLoader._save_light_info_base(data_stream, light_data)

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
        file_name_bytes = sound_data["fileName"].encode("utf-8")
        write_string(data_stream, file_name_bytes)

        # Write play state (boolean)
        data_stream.write(struct.pack("b", int(sound_data["play"])))

    # ============================================================
    # 6. UTILITY METHODS
    # ============================================================
    """
    General utility methods.

    - _parse_color_json: Parse JSON color strings to dictionaries
    - _compare_versions: Compare version strings for compatibility checks

    These methods delegate to KoikatuSceneObjectLoader for consistency
    across the codebase.
    """

    @staticmethod
    def _parse_color_json(json_str):
        """Parse color from JSON string"""
        return KoikatuSceneObjectLoader.parse_color_json(json_str)

    @staticmethod
    def _compare_versions(version1, version2):
        """Delegate to KoikatuSceneObjectLoader for consistency"""
        return KoikatuSceneObjectLoader._compare_versions(version1, version2)
