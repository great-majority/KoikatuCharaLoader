import argparse
import copy

from kkloader import KoikatuSceneData


def search_characters_from_scene(filename):
    """
    Load a Koikatu scene file and extract all character data.

    Uses KoikatuSceneData to properly parse the scene structure
    and extract character objects (type 0) including nested children.
    """
    scene = KoikatuSceneData.load(filename)

    charas = []
    # Use walk() with type filter to iterate character objects including nested children
    for _, obj_info in scene.walk(object_type=KoikatuSceneData.CHARACTER):
        chara = obj_info["data"]["character"]
        charas.append(chara)

    return charas


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Koikatu scene file (.png)")
    parser.add_argument("output_dir", help="output directory")
    args = parser.parse_args()

    charas = search_characters_from_scene(args.input)

    for c in charas:
        print(c)
        # use face png data instead of png data.
        c.image = copy.deepcopy(c.face_image)
        name = "{}{}({})".format(
            c["Parameter"]["lastname"],
            c["Parameter"]["firstname"],
            c["Parameter"]["nickname"],
        )
        c.save("{}/{}.png".format(args.output_dir, name))


if __name__ == "__main__":
    main()
