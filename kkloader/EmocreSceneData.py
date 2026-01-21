"""EmotionCreators scene data loader."""

import io
from typing import Self

from kkloader.EmocreCharaData import EmocreCharaData
from kkloader.EmocreMapData import EmocreMapData
from kkloader.funcs import get_png, load_length, load_type


class EmocreSceneData:
    """Class for loading EmotionCreators scene data.

    Attributes:
        png_data: PNG image data.
        product_no: Product number identifier.
        header: Header string as bytes.
        version: Version string as bytes.
        language: Language identifier.
        userid: User ID as bytes.
        dataid: Data ID as bytes.
        title: Scene title as bytes.
        comment: Scene comment as bytes.
        defaultbgm: Default BGM identifier.
        tags: List of tag identifiers.
        males: Number of male characters.
        females: Number of female characters.
        charas: List of EmocreCharaData instances.
        maps: List of EmocreMapData instances.
    """

    def __init__(self) -> None:
        """Initialize an EmocreSceneData instance."""
        pass

    @classmethod
    def load(cls, filelike: str | bytes | io.BytesIO) -> Self:
        """Load EmotionCreators scene data from a file or bytes.

        Args:
            filelike: Path to the file, bytes, or BytesIO object.

        Returns:
            A new EmocreSceneData instance with loaded data.

        Raises:
            ValueError: If the input type is not supported.
        """
        es = cls()

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

        es.png_data = get_png(data_stream)
        es.product_no = load_type(data_stream, "i")
        es.header = load_length(data_stream, "b")
        es.version = load_length(data_stream, "b")

        es.language = load_type(data_stream, "i")
        es.userid = load_length(data_stream, "b")
        es.dataid = load_length(data_stream, "b")
        es.title = load_length(data_stream, "b")
        es.comment = load_length(data_stream, "b")
        es.defaultbgm = load_type(data_stream, "i")
        es.tags = []
        length = load_type(data_stream, "i")
        for _ in range(length):
            es.tags.append(load_type(data_stream, "i"))
        es.males = load_type(data_stream, "i")
        es.females = load_type(data_stream, "i")
        es.isplaying = load_type(data_stream, "b")
        es.uses_adv = load_type(data_stream, "b")
        es.uses_hpart = load_type(data_stream, "b")
        length = load_type(data_stream, "i")
        es.charapackages = []
        for _ in range(length):
            es.charapackages.append(load_type(data_stream, "i"))
        length = load_type(data_stream, "i")
        es.mappackages = []
        for _ in range(length):
            es.mappackages.append(load_type(data_stream, "i"))
        es.uses_mapset = load_type(data_stream, "b")
        es.mapobjects = load_type(data_stream, "i")

        length = load_type(data_stream, "i")
        es.charas = []
        for _ in range(length):
            chara = EmocreCharaData.load(data_stream)
            es.charas.append(chara)

        length = load_type(data_stream, "i")
        es.maps = []
        for _ in range(length):
            map_data = EmocreMapData.load(data_stream, contains_png=False)
            es.maps.append(map_data)

        return es
