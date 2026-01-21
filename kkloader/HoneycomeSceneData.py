"""Honeycome scene data loader and saver."""

import io
import struct
from typing import Any, Self

from kkloader.funcs import get_png, load_string, load_type, write_string
from kkloader.HoneycomeSceneObjectLoader import HoneycomeSceneObjectLoader


class HoneycomeSceneData:
    """Class for loading and parsing Honeycome scene data.

    This implementation focuses on loading objects (items and folders) only.
    Supports both load and save operations.

    Attributes:
        image: PNG image data.
        version: Scene version string.
        dataVersion: Data format version string.
        user_id: User ID string.
        data_id: Data ID string.
        title: Scene title.
        objects: Dictionary of scene objects keyed by object ID.
        unknown_tail: Remaining unparsed data (lights, camera, etc.).
    """

    def __init__(self) -> None:
        """Initialize scene data with default values."""
        self.image: bytes | None = None
        self.version: str | None = None
        self.dataVersion: str | None = None
        self.user_id: str | None = None
        self.data_id: str | None = None
        self.title: str | None = None
        self.unknown_1: int | None = None
        self.unknown_2: int | None = None
        self.unknown_3: bytes | None = None
        self.objects: dict[int, dict[str, Any]] = {}
        self.unknown_tail: bytes = b""

    @classmethod
    def load(cls, filelike: str | bytes | io.BytesIO) -> Self:
        """
        Load Honeycome scene data from a file or bytes.

        Args:
            filelike: Path to the file, bytes, or BytesIO object containing the scene data

        Returns:
            HoneycomeSceneData: The loaded scene data
        """
        hs = cls()

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

        # Read PNG image
        hs.image = get_png(data_stream)

        # Read version string
        version_str = load_string(data_stream).decode("utf-8")

        # Read Honeycome-specific header fields
        hs.user_id = load_string(data_stream).decode("utf-8")
        hs.data_id = load_string(data_stream).decode("utf-8")
        hs.title = load_string(data_stream).decode("utf-8")

        # Read unknown fields
        hs.unknown_1 = load_type(data_stream, "i")  # 1
        hs.unknown_2 = load_type(data_stream, "i")
        hs.unknown_3 = data_stream.read(hs.unknown_2)

        hs.version = version_str
        hs.dataVersion = version_str

        # Read object dictionary
        obj_count = load_type(data_stream, "i")
        for _ in range(obj_count):
            key = load_type(data_stream, "i")
            obj_type = load_type(data_stream, "i")

            # Create object info based on type
            obj_info = {"type": obj_type, "data": {}}

            # Load object data based on type (only item and folder)
            HoneycomeSceneObjectLoader._dispatch_load(data_stream, obj_type, obj_info, version_str)

            hs.objects[key] = obj_info

        # Read remaining data as unknown_tail (lights, camera, etc.)
        hs.unknown_tail = data_stream.read()

        return hs

    def save(self, filelike: str | io.BytesIO) -> None:
        """
        Save Honeycome scene data to a file or BytesIO object.

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

        # Write version string
        version_bytes = self.version.encode("utf-8")
        data_stream.write(struct.pack("b", len(version_bytes)))
        data_stream.write(version_bytes)

        # Write Honeycome-specific header fields
        write_string(data_stream, self.user_id.encode("utf-8"))
        write_string(data_stream, self.data_id.encode("utf-8"))
        write_string(data_stream, self.title.encode("utf-8"))

        # Write unknown fields
        data_stream.write(struct.pack("i", self.unknown_1))
        data_stream.write(struct.pack("i", self.unknown_2))
        data_stream.write(self.unknown_3)

        # Write object dictionary
        data_stream.write(struct.pack("i", len(self.objects)))
        for key, obj_info in self.objects.items():
            data_stream.write(struct.pack("i", key))
            data_stream.write(struct.pack("i", obj_info["type"]))

            # Save object data based on type
            try:
                HoneycomeSceneObjectLoader._dispatch_save(data_stream, obj_info, self.version)
            except NotImplementedError as e:
                raise NotImplementedError(f"Cannot save object of type {obj_info['type']}: {str(e)}")

        # Write unknown_tail (lights, camera, etc.)
        data_stream.write(self.unknown_tail)

        return data_stream.getvalue()

    def walk(self, include_depth: bool = False):
        """
        Recursively iterate over all objects in the scene, including nested child objects.

        This method traverses the entire object hierarchy, yielding each object
        in depth-first order. It handles the different child structures for
        different object types:
        - Character (type 0): child is Dict[int, List[ObjectInfo]]
        - Item (type 1), Folder (type 3), Route (type 4): child is List[ObjectInfo]
        - Light (type 2), Camera (type 5): no children

        Args:
            include_depth: If True, yields (key, obj_info, depth) tuples.
                          If False, yields (key, obj_info) tuples.

        Yields:
            If include_depth is False:
                tuple: (key, obj_info) where key is the object's key/index
                       and obj_info is the object dictionary with 'type' and 'data'.
            If include_depth is True:
                tuple: (key, obj_info, depth) where depth indicates nesting level
                       (0 for top-level objects).

        Example:
            >>> scene = HoneycomeSceneData.load("scene.png")
            >>> for key, obj in scene.walk():
            ...     print(f"Object {key}: type={obj['type']}")
            >>> # With depth:
            >>> for key, obj, depth in scene.walk(include_depth=True):
            ...     print(f"{'  ' * depth}Object {key}: type={obj['type']}")
        """

        def _walk_children(obj_info, depth):
            """Recursively walk through child objects."""
            data = obj_info.get("data", {})
            child = data.get("child")

            if child is None:
                return

            obj_type = obj_info.get("type")

            # Character type (0) has Dict[int, List[ObjectInfo]] structure
            if obj_type == 0:
                for child_key, child_list in child.items():
                    for idx, child_obj in enumerate(child_list):
                        if include_depth:
                            yield (child_key, idx), child_obj, depth + 1
                        else:
                            yield (child_key, idx), child_obj
                        yield from _walk_children(child_obj, depth + 1)
            else:
                # Item (1), Folder (3), Route (4) have List[ObjectInfo] structure
                for idx, child_obj in enumerate(child):
                    if include_depth:
                        yield idx, child_obj, depth + 1
                    else:
                        yield idx, child_obj
                    yield from _walk_children(child_obj, depth + 1)

        # Iterate over top-level objects
        for key, obj_info in self.objects.items():
            if include_depth:
                yield key, obj_info, 0
            else:
                yield key, obj_info
            yield from _walk_children(obj_info, 0)

    def to_dict(self):
        """Convert the scene data to a dictionary"""
        return {
            "version": self.version,
            "dataVersion": self.dataVersion,
            "user_id": self.user_id,
            "data_id": self.data_id,
            "title": self.title,
            "objectCount": len(self.objects),
        }

    def __str__(self):
        """String representation of the scene data"""
        return f"HoneycomeSceneData(version={self.version}, objects={len(self.objects)})"
