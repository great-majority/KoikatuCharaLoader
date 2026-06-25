"""EmotionCreators scene data loader and saver.

EmotionCreators H/ADV scene files are PNG images with binary scene data
appended after the PNG IEND chunk. This module parses the scene header,
metadata, embedded characters, and embedded maps. The remaining HPart,
ADVPart, and node graph payload is preserved as opaque bytes so files can
round-trip without losing data while those subformats are implemented.
"""

import io
import os
import struct
from typing import Any, Self

from kkloader.EmocreCharaData import EmocreCharaData
from kkloader.EmocreMapData import EmocreMapData
from kkloader.funcs import get_png, load_string, load_type, write_string


def _version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def _version_ge(version: str, other: str) -> bool:
    left = _version_tuple(version)
    right = _version_tuple(other)
    size = max(len(left), len(right))
    return left + (0,) * (size - len(left)) >= right + (0,) * (size - len(right))


def _version_gt(version: str, other: str) -> bool:
    left = _version_tuple(version)
    right = _version_tuple(other)
    size = max(len(left), len(right))
    return left + (0,) * (size - len(left)) > right + (0,) * (size - len(right))


def _version_le(version: str, other: str) -> bool:
    left = _version_tuple(version)
    right = _version_tuple(other)
    size = max(len(left), len(right))
    return left + (0,) * (size - len(left)) <= right + (0,) * (size - len(right))


def _value_payload(value: Any) -> Any:
    """Return a recursively comparable payload, excluding raw byte caches."""
    if isinstance(value, (str, int, float, bool, bytes, type(None))):
        return value
    if isinstance(value, list | tuple):
        return [_value_payload(item) for item in value]
    if isinstance(value, dict):
        return {key: _value_payload(item) for key, item in value.items()}
    if hasattr(value, "__dict__"):
        return {
            key: _value_payload(item)
            for key, item in value.__dict__.items()
            if key
            not in {
                "raw_bytes",
                "_scene_raw_bytes",
                "_part_and_graph_data",
                "_force_reserialize",
                "original_filename",
                "modules",
            }
        }
    return value


class ValueComparable:
    """Mixin for object equality based on parsed values, not raw caches."""

    def value_payload(self) -> Any:
        return _value_payload(self)

    def __eq__(self, other: object) -> bool:
        if other.__class__ is not self.__class__:
            return NotImplemented
        return self.value_payload() == _value_payload(other)


def _read_bool(data_stream: io.BytesIO) -> bool:
    return bool(load_type(data_stream, "b"))


def _read_vector2(data_stream: io.BytesIO) -> dict[str, float]:
    return {"x": load_type(data_stream, "f"), "y": load_type(data_stream, "f")}


def _read_vector3(data_stream: io.BytesIO) -> dict[str, float]:
    return {"x": load_type(data_stream, "f"), "y": load_type(data_stream, "f"), "z": load_type(data_stream, "f")}


def _read_quaternion(data_stream: io.BytesIO) -> dict[str, float]:
    return {"x": load_type(data_stream, "f"), "y": load_type(data_stream, "f"), "z": load_type(data_stream, "f"), "w": load_type(data_stream, "f")}


def _read_position_rotation(data_stream: io.BytesIO) -> dict[str, Any]:
    return {"pos": _read_vector3(data_stream), "rot": _read_quaternion(data_stream)}


def _read_amount(data_stream: io.BytesIO) -> dict[str, Any]:
    return {"pos": _read_vector3(data_stream), "rot": _read_vector3(data_stream)}


def _read_change_amount(data_stream: io.BytesIO) -> dict[str, str]:
    return {
        "pos": load_string(data_stream).decode("utf-8"),
        "rot": load_string(data_stream).decode("utf-8"),
        "scale": load_string(data_stream).decode("utf-8"),
    }


def _read_camera_data(data_stream: io.BytesIO) -> dict[str, Any]:
    return {
        "pos": _read_vector3(data_stream),
        "dir": _read_vector3(data_stream),
        "rot": _read_vector3(data_stream),
        "fov": load_type(data_stream, "f"),
    }


def _read_screen_camera_info(data_stream: io.BytesIO) -> dict[str, Any]:
    return {
        "pos": _read_vector3(data_stream),
        "rotate": _read_quaternion(data_stream),
        "fov": load_type(data_stream, "f"),
    }


def _read_image_effect_info(data_stream: io.BytesIO) -> dict[str, Any]:
    return {
        "version": load_string(data_stream).decode("utf-8"),
        "color_effect": {"effect": load_type(data_stream, "i"), "blend": load_type(data_stream, "f")},
        "occlusion": {"is_use": _read_bool(data_stream), "color": {"r": load_type(data_stream, "f"), "g": load_type(data_stream, "f"), "b": load_type(data_stream, "f")}, "length": load_type(data_stream, "f")},
        "depth_of_field": {"is_use": _read_bool(data_stream), "focal_size": load_type(data_stream, "f"), "aperture": load_type(data_stream, "f")},
        "bloom": {"is_use": _read_bool(data_stream), "intensity": load_type(data_stream, "f"), "threshold": load_type(data_stream, "f"), "blur": load_type(data_stream, "f")},
        "sun_shafts": {
            "is_use": _read_bool(data_stream),
            "threshold": {"r": load_type(data_stream, "f"), "g": load_type(data_stream, "f"), "b": load_type(data_stream, "f")},
            "color": {"r": load_type(data_stream, "f"), "g": load_type(data_stream, "f"), "b": load_type(data_stream, "f")},
            "pos": _read_vector3(data_stream),
        },
        "vignette": {"is_use": _read_bool(data_stream)},
        "self_shadow": {"is_use": _read_bool(data_stream)},
        "blur": {"is_use": _read_bool(data_stream), "iterations": load_type(data_stream, "i"), "spread": load_type(data_stream, "f")},
    }


def _read_light_info(data_stream: io.BytesIO) -> dict[str, Any]:
    return {
        "version": load_string(data_stream).decode("utf-8"),
        "color": {"r": load_type(data_stream, "f"), "g": load_type(data_stream, "f"), "b": load_type(data_stream, "f"), "a": load_type(data_stream, "f")},
        "rot": _read_vector2(data_stream),
        "intensity": load_type(data_stream, "f"),
        "is_self_shadow": _read_bool(data_stream),
    }


def _read_camera_image_effect_info(data_stream: io.BytesIO, data_version: str) -> dict[str, Any]:
    result = {
        "camera": _read_camera_data(data_stream),
        "image_effect": _read_image_effect_info(data_stream),
        "lights": [_read_light_info(data_stream), _read_light_info(data_stream)],
        "bgm": {"id": load_type(data_stream, "i")},
        "screen_camera": None,
    }
    if _version_ge(data_version, "0.0.1.5"):
        result["screen_camera"] = _read_screen_camera_info(data_stream)
    return result


def _read_face(data_stream: io.BytesIO, data_version: str, is_all_version: bool = True) -> dict[str, Any]:
    result = {
        "eyeblow": load_type(data_stream, "i"),
        "eye": load_type(data_stream, "i"),
        "eye_open": load_type(data_stream, "f"),
    }
    if _version_ge(data_version, "0.0.1.11") if is_all_version else _version_ge(data_version, "0.0.1.0"):
        result["eyes_blink"] = _read_bool(data_stream)
    result.update(
        {
            "mouth": load_type(data_stream, "i"),
            "mouth_open": load_type(data_stream, "f"),
            "highlight": _read_bool(data_stream),
            "tear": load_type(data_stream, "i"),
            "cheek": load_type(data_stream, "f"),
            "eyes_line": load_type(data_stream, "i"),
            "eyes_line_rate": load_type(data_stream, "f"),
            "neck": load_type(data_stream, "i"),
            "neck_rate": load_type(data_stream, "f"),
            "tongue": load_type(data_stream, "i"),
            "tongue_animation_type": load_type(data_stream, "i"),
        }
    )
    if _version_ge(data_version, "0.0.1.13") if is_all_version else _version_ge(data_version, "0.0.1.1"):
        result["tongue_anime"] = load_type(data_stream, "i")
        result["tongue_anime_rate"] = load_type(data_stream, "f")
    return result


def _read_pose_info(data_stream: io.BytesIO) -> dict[str, Any]:
    pose_version: str
    result: dict[str, Any] = {
        "product_no": load_type(data_stream, "i"),
        "header": load_string(data_stream).decode("utf-8"),
    }
    pose_version = load_string(data_stream).decode("utf-8")
    result["version"] = pose_version
    result["uuid"] = load_string(data_stream).decode("utf-8")
    result["puid"] = load_string(data_stream).decode("utf-8")
    result["packages"] = [load_type(data_stream, "i") for _ in range(load_type(data_stream, "i"))]
    result["name"] = load_string(data_stream).decode("utf-8")
    result["language"] = load_type(data_stream, "i")
    result["anime_no"] = load_type(data_stream, "i")
    result["mode"] = load_type(data_stream, "i")
    result["used_fk_breast"] = _read_bool(data_stream)
    result["used_ik"] = [_read_bool(data_stream) for _ in range(9)] if _version_ge(pose_version, "0.0.2") else []
    result["used_fk_son"] = _read_bool(data_stream) if _version_ge(pose_version, "0.0.3") else False
    if _version_ge(pose_version, "1.0.0"):
        result["used_fk_hair"] = _read_bool(data_stream)
        result["hair_ids"] = [load_type(data_stream, "i") for _ in range(3)] if _version_ge(pose_version, "1.0.1") else []
        result["used_fk_skirt"] = _read_bool(data_stream)
        result["joint_correction"] = [_read_bool(data_stream) for _ in range(8)]
    result["hand_states"] = [{"hand": load_type(data_stream, "i"), "patterns": [load_type(data_stream, "i"), load_type(data_stream, "i")], "rate": load_type(data_stream, "i")} for _ in range(2)]
    result["fk_bones"] = _read_pose_bones(data_stream)
    result["ik_bones"] = _read_pose_bones(data_stream)
    return result


def _read_pose_bones(data_stream: io.BytesIO) -> list[dict[str, Any]]:
    bones = []
    for _ in range(load_type(data_stream, "i")):
        bones.append({"key": load_type(data_stream, "i"), "change_amount": _read_change_amount(data_stream)})
    return bones


def _read_adv_coordinate_info(data_stream: io.BytesIO) -> dict[str, Any]:
    result = {"type": load_type(data_stream, "B")}
    if result["type"] == 1:
        result["name"] = load_string(data_stream).decode("utf-8")
        result["data"] = data_stream.read(load_type(data_stream, "i"))
        result["version"] = load_string(data_stream).decode("utf-8")
        result["packages"] = [load_type(data_stream, "i") for _ in range(load_type(data_stream, "i"))]
    return result


def _read_h_coordinate_info(data_stream: io.BytesIO) -> dict[str, Any]:
    return {
        "coordinate_change": load_type(data_stream, "B"),
        "version": load_string(data_stream).decode("utf-8"),
        "name": load_string(data_stream).decode("utf-8"),
        "data": data_stream.read(load_type(data_stream, "i")),
        "packages": [load_type(data_stream, "i") for _ in range(load_type(data_stream, "i"))],
    }


def _read_adv_voice(data_stream: io.BytesIO) -> dict[str, Any]:
    return {
        "type": load_type(data_stream, "i"),
        "breath": {"category": load_type(data_stream, "i"), "id": load_type(data_stream, "i")},
        "voice_set": _read_adv_voice_set(data_stream),
    }


def _read_adv_voice_set(data_stream: io.BytesIO) -> dict[str, Any]:
    result = {"title": load_string(data_stream).decode("utf-8"), "version": load_string(data_stream).decode("utf-8")}
    result["datas"] = [{"category": load_type(data_stream, "i"), "id": load_type(data_stream, "i"), "state": load_type(data_stream, "i")} for _ in range(load_type(data_stream, "i"))]
    result["time_interval_min"] = load_type(data_stream, "f")
    result["time_interval_max"] = load_type(data_stream, "f")
    return result


def _read_motion(data_stream: io.BytesIO, data_version: str) -> dict[str, Any]:
    return {
        "amount": _read_amount(data_stream),
        "animation": _read_motion_animation(data_stream, data_version),
        "voice": _read_motion_voice(data_stream, data_version),
        "face_mens": _read_face(data_stream, data_version),
        "ik": _read_motion_ik(data_stream, data_version),
        "item": _read_motion_item(data_stream, data_version),
        "se": _read_motion_se(data_stream, data_version),
        "hand": _read_motion_hand(data_stream, data_version),
        "expression": {name: _read_bool(data_stream) for name in ["right_hand", "right_forearm", "left_hand", "left_forearm", "right_leg", "right_thighs", "left_leg", "left_thighs"]},
        "dankon": {
            "select": load_type(data_stream, "i"),
            "visible_son": _read_bool(data_stream),
            "parent_chara_id": load_type(data_stream, "i"),
            "parent_area": load_type(data_stream, "i"),
            "is_stick": _read_bool(data_stream),
            "rot_x": load_type(data_stream, "f"),
            "rot_y": load_type(data_stream, "f"),
        },
        "etc": {},
    }


def _read_motion_animation(data_stream: io.BytesIO, data_version: str) -> dict[str, Any]:
    return {
        "category": load_type(data_stream, "i"),
        "id": load_type(data_stream, "i"),
        "type": load_type(data_stream, "i"),
        "wait_parameter": load_type(data_stream, "f"),
        "state_play_time": load_type(data_stream, "f"),
        "paizuri_play_time": load_type(data_stream, "f"),
        "siru_uses": [_read_bool(data_stream) for _ in range(load_type(data_stream, "i"))],
        "siru_timing": [load_type(data_stream, "f") for _ in range(load_type(data_stream, "i"))],
        "layers": [{"weight": load_type(data_stream, "f"), "state": load_type(data_stream, "i"), "init_weight": load_type(data_stream, "f")} for _ in range(load_type(data_stream, "i"))],
        "correction_joints": [_read_vector3(data_stream) for _ in range(load_type(data_stream, "i"))],
    }


def _read_motion_voice(data_stream: io.BytesIO, data_version: str) -> dict[str, Any]:
    return {
        "breaths": [{"data": {"category": load_type(data_stream, "i"), "id": load_type(data_stream, "i")}, "face": _read_face(data_stream, data_version)} for _ in range(load_type(data_stream, "i"))],
        "voice_sets": [_read_voice_set_motion(data_stream, data_version) for _ in range(load_type(data_stream, "i"))],
        "time_random_min": load_type(data_stream, "f"),
        "time_random_max": load_type(data_stream, "f"),
    }


def _read_voice_set_motion(data_stream: io.BytesIO, data_version: str) -> dict[str, Any]:
    return {"sets": [_read_h_voice_set(data_stream, data_version) for _ in range(load_type(data_stream, "i"))], "is_use": _read_bool(data_stream)}


def _read_h_voice_set(data_stream: io.BytesIO, data_version: str) -> dict[str, Any]:
    return {
        "datas": [{"category": load_type(data_stream, "i"), "id": load_type(data_stream, "i"), "state": load_type(data_stream, "i")} for _ in range(load_type(data_stream, "i"))],
        "face": _read_face(data_stream, data_version),
        "is_use": _read_bool(data_stream),
        "is_part_once": _read_bool(data_stream),
        "is_motion_once": _read_bool(data_stream),
        "time_interval_min": load_type(data_stream, "f"),
        "time_interval_max": load_type(data_stream, "f"),
    }


def _read_motion_ik(data_stream: io.BytesIO, data_version: str) -> dict[str, Any]:
    return {
        "areas": [
            {"amount": _read_amount(data_stream), "is_use": _read_bool(data_stream), "weight": load_type(data_stream, "f"), "parent_chara_id": load_type(data_stream, "i"), "parent_area": load_type(data_stream, "i")}
            for _ in range(load_type(data_stream, "i"))
        ],
        "is_use": _read_bool(data_stream),
    }


def _read_motion_item(data_stream: io.BytesIO, data_version: str) -> dict[str, Any]:
    return {"infos": [{"item": load_type(data_stream, "i"), "is_se": _read_bool(data_stream)} for _ in range(load_type(data_stream, "i"))]}


def _read_motion_se(data_stream: io.BytesIO, data_version: str) -> dict[str, Any]:
    result = {"se": load_type(data_stream, "i"), "is_play": _read_bool(data_stream), "timing": load_type(data_stream, "f")}
    result["timing_kind"] = load_type(data_stream, "i") if _version_ge(data_version, "0.0.1.3") else 0
    return result


def _read_motion_hand(data_stream: io.BytesIO, data_version: str) -> dict[str, Any]:
    return {"infos": [{"use": load_type(data_stream, "i"), "base_ptn": load_type(data_stream, "i"), "add_ptn": load_type(data_stream, "i"), "blend": load_type(data_stream, "f")} for _ in range(load_type(data_stream, "i"))]}


def _read_map_item_state(data_stream: io.BytesIO) -> dict[str, Any]:
    result = {
        "kind": load_type(data_stream, "i"),
        "dic_key": load_type(data_stream, "i"),
        "change_amount": _read_change_amount(data_stream),
        "tree_state": load_type(data_stream, "i"),
        "visible": _read_bool(data_stream),
        "package": load_type(data_stream, "i"),
        "no": load_type(data_stream, "i"),
        "anime_speed": load_type(data_stream, "f"),
        "colors": [load_string(data_stream).decode("utf-8") for _ in range(8)],
        "patterns": [{"key": load_type(data_stream, "i"), "clamp": _read_bool(data_stream), "uv": load_string(data_stream).decode("utf-8"), "rot": load_type(data_stream, "f")} for _ in range(3)],
        "alpha": load_type(data_stream, "f"),
        "line_color": load_string(data_stream).decode("utf-8"),
        "line_width": load_type(data_stream, "f"),
        "emission_color": load_string(data_stream).decode("utf-8"),
        "emission_power": load_type(data_stream, "f"),
        "light_cancel": load_type(data_stream, "f"),
        "pillar": {"dic_key": load_type(data_stream, "i"), "change_amount": _read_change_amount(data_stream)},
        "shielding": _read_bool(data_stream),
    }
    # ADV item states are initialized with ten fixed item slots and should not
    # normally contain children, but the serialized OIItem format includes a
    # child count.
    result["children_raw"] = []
    for _ in range(load_type(data_stream, "i")):
        child_start = data_stream.tell()
        raise NotImplementedError(f"Unsupported child item in ADV item state at byte {child_start}")
    return result


class RawSerializable(ValueComparable):
    """Base class for parsed objects that preserve exact source bytes."""

    def __init__(self) -> None:
        self.raw_bytes: bytes | None = None
        self._force_reserialize = False

    def __bytes__(self) -> bytes:
        if self.raw_bytes is not None and not self._force_reserialize:
            return self.raw_bytes
        raise NotImplementedError(f"{self.__class__.__name__} does not implement mutation serialization yet")


class ScenePart(RawSerializable):
    """Base HEdit scene part."""

    def __init__(self) -> None:
        super().__init__()
        self.key = ""
        self.kind = 0
        self.uuid = ""
        self.name = ""
        self.is_init = False
        self.use_map_id = 0

    def _load_base(self, data_stream: io.BytesIO, data_version: str) -> None:
        self.uuid = load_string(data_stream).decode("utf-8")
        self.name = load_string(data_stream).decode("utf-8")
        self.kind = load_type(data_stream, "i")
        self.is_init = _read_bool(data_stream)
        if _version_ge(data_version, "0.0.1.10"):
            self.use_map_id = load_type(data_stream, "i")


class HPart(ScenePart):
    """Structured HPart data."""

    @classmethod
    def load(cls, data_stream: io.BytesIO, data_version: str, key: str) -> "HPart":
        start = data_stream.tell()
        part = cls()
        part.key = key
        part._load_base(data_stream, data_version)
        part.groups = [_read_h_group(data_stream, data_version) for _ in range(load_type(data_stream, "i"))]
        part.camera_image = _read_camera_image_effect_info(data_stream, data_version)
        part.coordinate_infos = []
        part.coordinate_package = []
        if _version_ge(data_version, "1.0.2.0"):
            part.coordinate_infos = [_read_h_coordinate_info(data_stream) for _ in range(load_type(data_stream, "i"))]
            part.coordinate_package = [load_type(data_stream, "i") for _ in range(load_type(data_stream, "i"))]
        part.raw_bytes = data_stream.getbuffer()[start : data_stream.tell()].tobytes()
        return part


def _read_h_group(data_stream: io.BytesIO, data_version: str) -> dict[str, Any]:
    return {
        "title": load_string(data_stream).decode("utf-8"),
        "amount": _read_amount(data_stream),
        "characters": [_read_h_part_chara_info(data_stream, data_version) for _ in range(load_type(data_stream, "i"))],
        "motions": [{"is_use": _read_bool(data_stream), "name": load_string(data_stream).decode("utf-8"), "finish_wait_time": load_type(data_stream, "f")} for _ in range(load_type(data_stream, "i"))],
        "is_sync": _read_bool(data_stream),
        "is_with_main_group": _read_bool(data_stream),
    }


def _read_h_part_chara_info(data_stream: io.BytesIO, data_version: str) -> dict[str, Any]:
    result = {"use_chara_id": load_type(data_stream, "i"), "motions": [_read_motion(data_stream, data_version) for _ in range(load_type(data_stream, "i"))]}
    result["start_part_cloth"] = load_type(data_stream, "i") if _version_ge(data_version, "0.0.1.12") else 0
    return result


class ADVPart(ScenePart):
    """Structured ADVPart data."""

    @classmethod
    def load(cls, data_stream: io.BytesIO, data_version: str, key: str) -> "ADVPart":
        start = data_stream.tell()
        part = cls()
        part.key = key
        part._load_base(data_stream, data_version)
        part.cuts = [_read_adv_cut(data_stream, data_version) for _ in range(load_type(data_stream, "i"))]
        part.screen_camera = _read_screen_camera_info(data_stream) if _version_ge(data_version, "1.0.1.0") else None
        part.raw_bytes = data_stream.getbuffer()[start : data_stream.tell()].tobytes()
        return part


def _read_adv_cut(data_stream: io.BytesIO, data_version: str) -> dict[str, Any]:
    result = {"end_cut": _read_bool(data_stream)}
    result["char_states"] = [_read_adv_char_state(data_stream, data_version) for _ in range(load_type(data_stream, "i"))]
    result["item_states"] = [_read_adv_item_state(data_stream, data_version) for _ in range(load_type(data_stream, "i"))] if _version_ge(data_version, "0.0.1.7") else []
    result["camera_image_effect"] = _read_camera_image_effect_info(data_stream, data_version)
    result["speech_bubbles"] = [_read_speech_bubble(data_stream, data_version) for _ in range(load_type(data_stream, "i"))]
    result["screen_effects"] = [_read_screen_effect(data_stream, data_version) for _ in range(load_type(data_stream, "i"))]
    result["fade"] = load_type(data_stream, "i")
    return result


def _read_adv_char_state(data_stream: io.BytesIO, data_version: str) -> dict[str, Any]:
    result = {
        "id": load_type(data_stream, "i"),
        "visible": _read_bool(data_stream),
        "position_rotation": _read_position_rotation(data_stream),
        "pose": _read_pose_info(data_stream),
        "face": _read_face(data_stream, data_version),
    }
    if _version_le(data_version, "0.0.1.4"):
        result["legacy_face_ids"] = [load_type(data_stream, "i"), load_type(data_stream, "i")]
    result["neck_add"] = load_string(data_stream).decode("utf-8") if _version_ge(data_version, "0.0.1.8") else ""
    result["coordinate"] = _read_adv_coordinate_info(data_stream) if _version_ge(data_version, "1.0.2.0") else {"type": 0}
    result["clothes"] = [load_type(data_stream, "i") for _ in range(8)]
    result["accessory"] = [load_type(data_stream, "i") for _ in range(20)] if _version_ge(data_version, "0.0.1.8") else []
    result["liquid"] = [load_type(data_stream, "i") for _ in range(5)]
    result["visible_sun"] = _read_bool(data_stream) if _version_ge(data_version, "0.0.1.16") else False
    result["voice"] = _read_adv_voice(data_stream) if _version_ge(data_version, "1.0.2.1") else None
    return result


def _read_adv_item_state(data_stream: io.BytesIO, data_version: str) -> dict[str, Any]:
    return {"parent_kind": load_type(data_stream, "i"), "parent_chara": load_type(data_stream, "i"), "item": _read_map_item_state(data_stream)}


def _read_speech_bubble(data_stream: io.BytesIO, data_version: str) -> dict[str, Any]:
    result = {}
    if _version_ge(data_version, "0.0.1.15"):
        result["sort_order"] = load_type(data_stream, "i")
    result.update(
        {
            "id": load_type(data_stream, "i"),
            "option": _read_bool(data_stream),
            "pos": load_string(data_stream).decode("utf-8"),
            "rot": load_type(data_stream, "f"),
            "size": load_string(data_stream).decode("utf-8"),
            "color": load_string(data_stream).decode("utf-8"),
            "outline_color": load_string(data_stream).decode("utf-8"),
            "outline_spread": load_type(data_stream, "f"),
            "text_layouts": [_read_text_layout(data_stream, data_version) for _ in range(2)],
        }
    )
    return result


def _read_text_layout(data_stream: io.BytesIO, data_version: str) -> dict[str, Any]:
    result = {"msg": load_string(data_stream).decode("utf-8")}
    if _version_ge(data_version, "0.0.1.0"):
        result["font"] = load_type(data_stream, "i")
    result["font_size"] = load_type(data_stream, "i")
    if _version_ge(data_version, "0.0.1.4"):
        result["line_spacing"] = load_type(data_stream, "f")
    if _version_ge(data_version, "0.0.1.9"):
        result["anime"] = _read_bool(data_stream)
    result["text_dir"] = load_type(data_stream, "i")
    if _version_ge(data_version, "1.0.2.2"):
        result["auto_line"] = _read_bool(data_stream)
    result["range"] = load_string(data_stream).decode("utf-8")
    result["rot"] = load_type(data_stream, "f")
    result["color"] = load_string(data_stream).decode("utf-8")
    if _version_ge(data_version, "0.0.1.1"):
        result["effect"] = load_type(data_stream, "i")
    result["outline_color"] = load_string(data_stream).decode("utf-8")
    result["outline_spread"] = load_type(data_stream, "f")
    return result


def _read_screen_effect(data_stream: io.BytesIO, data_version: str) -> dict[str, Any]:
    result = {}
    if _version_ge(data_version, "0.0.1.15"):
        result["sort_order"] = load_type(data_stream, "i")
    result.update(
        {
            "id": load_type(data_stream, "i"),
            "pos": load_string(data_stream).decode("utf-8"),
            "rot": load_type(data_stream, "f"),
            "size": load_string(data_stream).decode("utf-8"),
            "color": load_string(data_stream).decode("utf-8"),
            "outline_color": load_string(data_stream).decode("utf-8"),
            "outline_spread": load_type(data_stream, "f"),
        }
    )
    return result


class NodeControlData(RawSerializable):
    """Structured YS_Node.NodeControl payload."""

    @classmethod
    def load(cls, data: bytes, data_version: str) -> "NodeControlData":
        node_graph = cls()
        node_graph.raw_bytes = data
        data_stream = io.BytesIO(data)
        node_graph.grid_pos = _read_vector2(data_stream)
        node_graph.grid_scale = load_type(data_stream, "f")
        node_graph.nodes = [NodeBaseData.load(data_stream, data_version) for _ in range(load_type(data_stream, "i"))]
        return node_graph


class NodeBaseData(ValueComparable):
    """Structured YS_Node.NodeBase payload."""

    @classmethod
    def load(cls, data_stream: io.BytesIO, data_version: str) -> "NodeBaseData":
        node = cls()
        node.kind = load_type(data_stream, "i")
        node.uid = load_string(data_stream).decode("utf-8")
        node.name = load_string(data_stream).decode("utf-8")
        node.pos = _read_vector2(data_stream)
        node.end_condition_type = [load_type(data_stream, "i") for _ in range(5)]
        node.end_condition_count = [load_type(data_stream, "i") for _ in range(5)]
        node.child_uid = [load_string(data_stream).decode("utf-8") for _ in range(5)]
        node.fade_type = [load_type(data_stream, "i") for _ in range(5)] if _version_gt(data_version, "0.0.1.5") else [0] * 5
        node.fade_time = [load_type(data_stream, "f") for _ in range(5)] if _version_gt(data_version, "0.0.1.13") else [0.5] * 5
        return node


class EmocreSceneData(ValueComparable):
    """Class for loading and saving EmotionCreators H/ADV scene data.

    This is based on ``HEdit.HEditData.Save`` / ``Load`` in EmotionCreators.

    Attributes:
        image: PNG thumbnail bytes.
        product_no: Product number. EmotionCreators uses ``200``.
        header: Scene marker string, normally ``"【EroMakeHScene】"``.
        version: Scene data version string.
        info: Dictionary containing the HEditData.InfoData payload.
        charas: Embedded EmotionCreators character cards.
        maps: Embedded EmotionCreators map data, without PNG thumbnails.
        part_and_graph_data: Opaque bytes containing HPart/ADVPart data and
            the YS_Node graph payload.
    """

    HEADER = "【EroMakeHScene】"

    def __init__(self) -> None:
        """Initialize scene data with conservative defaults."""
        self.image: bytes | None = None
        self.product_no: int = 200
        self.header: str = self.HEADER
        self.version: str = "1.0.2.2"

        self.info: dict[str, Any] = {
            "language": 0,
            "user_id": "",
            "save_id": "",
            "title": "",
            "comment": "",
            "default_bgm": 2,
            "tags": [-1, -1, -1],
            "male_count": 0,
            "female_count": 0,
            "is_playing": False,
            "uses_adv": False,
            "uses_hpart": False,
            "chara_packages": [],
            "map_packages": [],
            "uses_mapset": False,
            "map_objects": 0,
        }

        self.charas: list[EmocreCharaData] = []
        self.maps: list[EmocreMapData] = []
        self.parts: list[ScenePart] = []
        self.node_graph: NodeControlData | None = None
        self._part_and_graph_data: bytes = b""
        self.original_filename: str | None = None

    @classmethod
    def load(cls, filelike: str | bytes | io.BytesIO) -> Self:
        """Load EmotionCreators scene data from a path, bytes, or stream."""
        scene = cls()

        if isinstance(filelike, str):
            with open(filelike, "br") as f:
                data = f.read()
            data_stream = io.BytesIO(data)
            scene.original_filename = os.path.abspath(filelike)
        elif isinstance(filelike, bytes):
            data_stream = io.BytesIO(filelike)
        elif isinstance(filelike, io.BytesIO):
            data_stream = filelike
        else:
            raise ValueError(f"Unsupported input type: {type(filelike)}")

        scene.image = get_png(data_stream)
        scene.product_no = load_type(data_stream, "i")
        scene.header = load_string(data_stream).decode("utf-8")
        if scene.header != cls.HEADER:
            raise ValueError(f"Unexpected EmotionCreators scene header: {scene.header!r}")
        scene.version = load_string(data_stream).decode("utf-8")

        scene._load_info(data_stream)
        scene._load_characters(data_stream)
        scene._load_maps(data_stream)
        scene._load_parts_and_node_graph(data_stream)

        return scene

    def save(self, filelike: str | io.BytesIO) -> None:
        """Save EmotionCreators scene data to a path or stream."""
        data = bytes(self)
        if isinstance(filelike, str):
            with open(filelike, "bw") as f:
                f.write(data)
        elif isinstance(filelike, io.BytesIO):
            filelike.write(data)
        else:
            raise ValueError(f"Unsupported output type: {type(filelike)}")

    def __bytes__(self) -> bytes:
        """Convert this scene to binary EmotionCreators scene bytes."""
        data_stream = io.BytesIO()

        if self.image:
            data_stream.write(self.image)

        data_stream.write(struct.pack("i", self.product_no))
        write_string(data_stream, self.header.encode("utf-8"))
        write_string(data_stream, self.version.encode("utf-8"))

        self._save_info(data_stream)

        data_stream.write(struct.pack("i", len(self.charas)))
        for chara in self.charas:
            data_stream.write(self._embedded_object_bytes(chara))

        data_stream.write(struct.pack("i", len(self.maps)))
        for map_data in self.maps:
            data_stream.write(self._embedded_object_bytes(map_data))

        data_stream.write(self.part_and_graph_data)
        return data_stream.getvalue()

    def to_dict(self, *, include_image: bool = False) -> dict[str, Any]:
        """Return a compact dictionary representation for inspection."""
        data: dict[str, Any] = {
            "product_no": self.product_no,
            "header": self.header,
            "version": self.version,
            "info": dict(self.info),
            "character_count": len(self.charas),
            "map_count": len(self.maps),
            "part_count": len(self.parts),
            "node_count": len(self.node_graph.nodes) if self.node_graph is not None else 0,
            "part_and_graph_data_size": len(self.part_and_graph_data),
            "original_filename": self.original_filename,
        }
        if include_image:
            data["image"] = self.image
        return data

    def __repr__(self) -> str:
        """Return a concise debug representation."""
        title = self.info.get("title", "")
        return (
            f"EmocreSceneData(product_no={self.product_no!r}, "
            f"header={self.header!r}, version={self.version!r}, "
            f"title={title!r}, charas={len(self.charas)}, maps={len(self.maps)}, "
            f"parts={len(self.parts)}, nodes={len(self.node_graph.nodes) if self.node_graph is not None else 0}, "
            f"part_and_graph_data_size={len(self.part_and_graph_data)}, "
            f"original_filename={self.original_filename!r})"
        )

    @property
    def part_and_graph_data(self) -> bytes:
        """Return serialized part and node graph bytes."""
        if self._part_and_graph_data and not any(getattr(part, "_force_reserialize", False) for part in self.parts) and not getattr(self.node_graph, "_force_reserialize", False):
            return self._part_and_graph_data

        data_stream = io.BytesIO()
        data_stream.write(struct.pack("i", len(self.parts)))
        for part in self.parts:
            write_string(data_stream, part.key.encode("utf-8"))
            data_stream.write(struct.pack("i", part.kind))
            data_stream.write(bytes(part))
        node_graph_bytes = bytes(self.node_graph) if self.node_graph is not None else b""
        data_stream.write(struct.pack("i", len(node_graph_bytes)))
        data_stream.write(node_graph_bytes)
        return data_stream.getvalue()

    @part_and_graph_data.setter
    def part_and_graph_data(self, value: bytes) -> None:
        self._part_and_graph_data = value

    def _load_info(self, data_stream: io.BytesIO) -> None:
        """Load HEditData.InfoData."""
        info = self.info
        info["language"] = load_type(data_stream, "i")
        info["user_id"] = load_string(data_stream).decode("utf-8")
        info["save_id"] = load_string(data_stream).decode("utf-8")
        info["title"] = load_string(data_stream).decode("utf-8")
        info["comment"] = load_string(data_stream).decode("utf-8")
        info["default_bgm"] = load_type(data_stream, "i")
        info["tags"] = [load_type(data_stream, "i") for _ in range(load_type(data_stream, "i"))]
        info["male_count"] = load_type(data_stream, "i")
        info["female_count"] = load_type(data_stream, "i")
        info["is_playing"] = bool(load_type(data_stream, "b"))
        info["uses_adv"] = bool(load_type(data_stream, "b"))
        info["uses_hpart"] = bool(load_type(data_stream, "b"))
        info["chara_packages"] = [load_type(data_stream, "i") for _ in range(load_type(data_stream, "i"))]
        info["map_packages"] = [load_type(data_stream, "i") for _ in range(load_type(data_stream, "i"))]
        info["uses_mapset"] = bool(load_type(data_stream, "b"))
        info["map_objects"] = load_type(data_stream, "i")

    def _save_info(self, data_stream: io.BytesIO) -> None:
        """Save HEditData.InfoData."""
        info = self.info
        data_stream.write(struct.pack("i", int(info["language"])))
        write_string(data_stream, str(info["user_id"]).encode("utf-8"))
        write_string(data_stream, str(info["save_id"]).encode("utf-8"))
        write_string(data_stream, str(info["title"]).encode("utf-8"))
        write_string(data_stream, str(info["comment"]).encode("utf-8"))
        data_stream.write(struct.pack("i", int(info["default_bgm"])))

        tags = list(info["tags"])
        data_stream.write(struct.pack("i", len(tags)))
        for tag in tags:
            data_stream.write(struct.pack("i", int(tag)))

        data_stream.write(struct.pack("i", int(info["male_count"])))
        data_stream.write(struct.pack("i", int(info["female_count"])))
        data_stream.write(struct.pack("b", int(bool(info["is_playing"]))))
        data_stream.write(struct.pack("b", int(bool(info["uses_adv"]))))
        data_stream.write(struct.pack("b", int(bool(info["uses_hpart"]))))

        chara_packages = list(info["chara_packages"])
        data_stream.write(struct.pack("i", len(chara_packages)))
        for package in chara_packages:
            data_stream.write(struct.pack("i", int(package)))

        map_packages = list(info["map_packages"])
        data_stream.write(struct.pack("i", len(map_packages)))
        for package in map_packages:
            data_stream.write(struct.pack("i", int(package)))

        data_stream.write(struct.pack("b", int(bool(info["uses_mapset"]))))
        data_stream.write(struct.pack("i", int(info["map_objects"])))

    def _load_characters(self, data_stream: io.BytesIO) -> None:
        """Load embedded EmotionCreators character cards."""
        self.charas = []
        for _ in range(load_type(data_stream, "i")):
            start_pos = data_stream.tell()
            chara = EmocreCharaData.load(data_stream)
            chara._scene_raw_bytes = data_stream.getbuffer()[start_pos : data_stream.tell()].tobytes()
            self.charas.append(chara)

    def _load_maps(self, data_stream: io.BytesIO) -> None:
        """Load embedded EmotionCreators map data without PNG thumbnails."""
        self.maps = []
        for _ in range(load_type(data_stream, "i")):
            start_pos = data_stream.tell()
            map_data = EmocreMapData.load(data_stream, contains_png=False)
            map_data._scene_raw_bytes = data_stream.getbuffer()[start_pos : data_stream.tell()].tobytes()
            self.maps.append(map_data)

    def _load_parts_and_node_graph(self, data_stream: io.BytesIO) -> None:
        """Load HPart/ADVPart records and the YS_Node graph payload."""
        start_pos = data_stream.tell()
        self.parts = []
        for _ in range(load_type(data_stream, "i")):
            key = load_string(data_stream).decode("utf-8")
            kind = load_type(data_stream, "i")
            if kind == 0:
                part = HPart.load(data_stream, self.version, key)
            elif kind == 1:
                part = ADVPart.load(data_stream, self.version, key)
            else:
                raise ValueError(f"Unknown EmotionCreators scene part kind: {kind}")
            self.parts.append(part)

        node_graph_bytes = data_stream.read(load_type(data_stream, "i"))
        self.node_graph = NodeControlData.load(node_graph_bytes, self.version)
        self._part_and_graph_data = data_stream.getbuffer()[start_pos : data_stream.tell()].tobytes()

    @staticmethod
    def _embedded_object_bytes(obj: Any) -> bytes:
        """Return exact embedded bytes when available, otherwise serialize."""
        raw_bytes = getattr(obj, "_scene_raw_bytes", None)
        if raw_bytes is not None and not getattr(obj, "_force_reserialize", False):
            return raw_bytes
        return bytes(obj)
