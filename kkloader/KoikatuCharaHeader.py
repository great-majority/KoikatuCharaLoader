"""Koikatu character header loader."""

import io
from typing import Optional, Union

from kkloader.funcs import get_png, load_length, load_type


class KoikatuCharaHeader:
    """Load only the header part of a Koikatu character file."""

    def __init__(self) -> None:
        """Initialize empty header fields."""
        self.image: Optional[bytes] = None
        self.product_no: int | None = None
        self.header: bytes | None = None
        self.version: bytes | None = None
        self.face_image: bytes | None = None

    @classmethod
    def load(cls, filelike: Union[str, bytes, io.BytesIO], contains_png: bool = True) -> "KoikatuCharaHeader":
        """Load the header portion from a Koikatu character file.

        Args:
            filelike: Path, bytes, or a BytesIO stream containing the data.
            contains_png: Whether the file starts with PNG image data.
        """
        kch = cls()

        if isinstance(filelike, str):
            with open(filelike, "br") as f:
                data = f.read()
            data_stream = io.BytesIO(data)

        elif isinstance(filelike, bytes):
            data_stream = io.BytesIO(filelike)

        elif isinstance(filelike, io.BytesIO):
            data_stream = filelike

        else:
            raise ValueError("unsupported input. type:{}".format(type(filelike)))

        kch.image: Optional[bytes] = None
        if contains_png:
            kch.image = get_png(data_stream)

        kch.product_no = load_type(data_stream, "i")  # 100
        kch.header = load_length(data_stream, "b")  # 【KoiKatuChara】
        kch.version = load_length(data_stream, "b")  # 0.0.0
        kch.face_image = load_length(data_stream, "i")

        return kch
