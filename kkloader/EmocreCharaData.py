"""EmotionCreators character data loader and saver."""

import io
import struct
from typing import Any

import kkloader
import kkloader.KoikatuCharaData
from kkloader.funcs import get_png, load_length, load_type


class EmocreCharaData(kkloader.KoikatuCharaData):
    """Character data class for EmotionCreators.

    Extends KoikatuCharaData with EmotionCreators-specific header fields
    including language, user ID, data ID, and packages.

    Attributes:
        language: Language identifier.
        userid: User ID as bytes.
        dataid: Data ID as bytes.
        packages: List of package identifiers.
    """

    language: int
    userid: bytes
    dataid: bytes
    packages: list[int]

    def __init__(self) -> None:
        """Initialize an EmocreCharaData instance with EmotionCreators block modules."""
        self.modules = {
            "Custom": kkloader.kk_Custom,
            "Coordinate": kkloader.kk_Coordinate,
            "Parameter": kkloader.kk_Parameter,
            "Status": kkloader.kk_Status,
            "About": kkloader.kk_About,
            "KKEx": kkloader.kk_KKEx,
        }

    def _load_header(self, data: io.BytesIO, **kwargs: Any) -> None:
        """Load EmotionCreators-specific header information.

        Args:
            data: BytesIO stream positioned at the start of the header.
            **kwargs: Additional keyword arguments (unused).
        """
        self.image = get_png(data)
        self.product_no = load_type(data, "i")
        self.header = load_length(data, "b")
        self.version = load_length(data, "b")
        self.language = load_type(data, "i")
        self.userid = load_length(data, "b")
        self.dataid = load_length(data, "b")
        package_length = load_type(data, "i")
        self.packages = []
        for _ in range(package_length):
            self.packages.append(load_type(data, "i"))

    def _make_bytes_header(self) -> bytes:
        """Create the binary header data for EmotionCreators format.

        Returns:
            Binary header including all EmotionCreators-specific fields.
        """
        ipack = struct.Struct("i")
        bpack = struct.Struct("b")
        packages = b"".join(list(map(lambda x: ipack.pack(x), self.packages)))
        data = b"".join(
            [
                self.image,
                ipack.pack(self.product_no),
                bpack.pack(len(self.header)),
                self.header,
                bpack.pack(len(self.version)),
                self.version,
                ipack.pack(self.language),
                bpack.pack(len(self.userid)),
                self.userid,
                bpack.pack(len(self.dataid)),
                self.dataid,
                ipack.pack(len(self.packages)),
                packages,
            ]
        )
        return data

    def _make_dict_header(self, **kwargs: Any) -> dict[str, Any]:
        """Create a dictionary representation of the EmotionCreators header.

        Args:
            **kwargs: Additional keyword arguments (unused).

        Returns:
            Dictionary containing all header information.
        """
        data: dict[str, Any] = {
            "product_no": self.product_no,
            "header": self.header.decode("utf-8"),
            "version": self.version.decode("utf-8"),
            "blockdata": self.blockdata,
            "userid": self.userid.decode("utf-8"),
            "dataid": self.dataid.decode("utf-8"),
            "language": self.language,
            "packages": self.packages,
        }
        return data

    def __str__(self) -> str:
        """Return a string representation of the EmotionCreators character.

        Returns:
            String containing header, name, user ID, and data ID.
        """
        header = self.header.decode("utf-8")
        userid = self.userid.decode("ascii")
        dataid = self.dataid.decode("ascii")
        return "{}, {}, userid:{}, dataid:{}".format(header, self["Parameter"]["fullname"], userid, dataid)
