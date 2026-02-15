# KoikatuCharaLoader
A simple deserializer and serializer for character and scene data from Koikatu, EmotionCreators, Honeycome, SummerVacationScramble and Aicomi.

[![](https://img.shields.io/pypi/v/kkloader)](https://pypi.org/project/kkloader/)
[![Downloads](https://static.pepy.tech/badge/kkloader)](https://pepy.tech/project/kkloader)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/great-majority/KoikatuCharaLoader/blob/master/notebooks/sandbox.ipynb)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/great-majority/KoikatuCharaLoader)

[日本語マニュアルがここにあります](README.ja.md)

# Installation
You can install the module from [PyPI](https://pypi.org/project/kkloader/).
```
$ pip install kkloader
```
If this doesn't work, try the following command (this is typically needed for Windows users).
```
$ python -m pip install kkloader
```

If you just want to quickly try out this module, you can click the "Open In Colab" button above to run it directly on Colab.

# Basic Usage
```python
$ python
>>> from kkloader import KoikatuCharaData # Import the module.
>>> kc = KoikatuCharaData.load("./data/kk_chara.png") # Load character data.
>>> kc
KoikatuCharaData(product_no=100, header='【KoiKatuChara】', version='0.0.0', name='白峰 一乃 ( かずのん )', blocks=['Custom', 'Coordinate', 'Parameter', 'Status'], has_kkex=False, original_file_path='/path/to/data/kk_chara.png')
>>> kc["Parameter"]["nickname"] # Print the character's nickname.
'かずのん'
>>> kc["Parameter"]["nickname"] = "chikarin" # Change the nickname.
>>> kc.save("./kk_chara_modified.png") # Save to `kk_chara_modified.png`.
```
That's it! :)

# List of Classes

- Supports saving and loading:
  - `KoikatuCharaData`
  - `KoikatuSceneData`
  - `EmocreCharaData`
  - `HoneycomeCharaData`
  - `SummerVacationCharaData`
  - `SummerVacationSaveData`
  - `AicomiCharaData`
  - `HoneycomeSceneData` (also compatible with DigitalCraft)
- Supports loading only:
  - `KoikatuSaveData`
  - `EmocreMapData`
  - `EmocreSceneData`

Any class can be imported with `from kkloader import KoikatuCharaData` and data can be loaded using the `.load(filename)` method.

# How Block Data Works

Koikatu character data consists of several *block data* sections. Each *block data* contains various character parameters. A typical Koikatu character data includes the following block data:

| name of blockdata | description                                                  |
| ----------------- | ------------------------------------------------------------ |
| Custom            | Values for the character's face, body, and hairstyle.        |
| Coordinate        | Values for clothes and accessories worn by characters.       |
| Parameter         | Values for character's name, birthday, preferences, etc.     |
| Status            | Values for clothed states, etc. (Usage in the game is unclear) |
| About             | userID & dataID (added from Koikatu Sunshine)                |
| KKEx              | Data used by mods                                            |

You can check which block data is present in `blockdata` from the `KoikatuCharaData` object:
```
>>> kc.blockdata
['Custom', 'Coordinate', 'Parameter', 'Status']
```
If there is block data in an unknown format, it can be found using `unknown_blockdata`.

### Accessing Block Data
The block data can be accessed either as a member variable of the `KoikatuCharaData` class or as a dictionary.
```python
>>> kc.Custom
<kkloader.KoikatuCharaData.Custom object at 0x7f406bf18460>
>>> kc["Custom"]
<kkloader.KoikatuCharaData.Custom object at 0x7f406bf18460>
```
As shown, both lines access the same `kc.Custom`.

### Find Variables

You can try out the character information display from this program in your browser on [this site](https://kk-snippets.streamlit.app/chara-data-viewer).
If you are looking to identify which variables to modify, this interface can serve as a useful starting point for narrowing down potential candidates.

![](https://i.imgur.com/E2hAdm1.png)

By using the `prettify` method, the contents of the variables within the data block will be displayed in a more readable format.
This is useful for identifying which variables exist.
```
>>> kc["Custom"].prettify()
{
  "face": {
    "version": "0.0.2",
    "shapeValueFace": [
      ...
    ],
    "headId": 0,
    "skinId": 0,
    "detailId": 0,
    "detailPower": 0.41674190759658813,
    ...
```

### KKEx MessagePack Handling

The `KKEx` in `blockdata` sometimes contains fields encoded as raw `bytes` that are themselves MessagePack payloads.  
kkloader automatically deserializes and reserializes such fields for known plugins listed in `KKEx.NESTED_KEYS`.


# Export to JSON file
```
from kkloader import KoikatuCharaData

k = KoikatuCharaData.load("./data/kk_chara.png")
k.save_json("data.json") 
```

`data.json`
```json
{
  "product_no": 100,
  "header": "\u3010KoiKatuChara\u3011",
  "version": "0.0.0",
  "Custom": {
    "face": {
      "version": "0.0.2",
      "shapeValueFace": [
        0.5403226017951965,
        1.0,
        0.2016129046678543,
        0.0,
        0.22580644488334656,
        0.0,
        0.0,
        0.1794193685054779,
        0.0,
...
```
If you add `include_image=True` to the `save_json` function's arguments, base64-encoded images will be included in the JSON output.

# Recipes

### Change Character Name
```python
from kkloader import KoikatuCharaData

k = KoikatuCharaData.load("./data/kk_chara.png")
k["Parameter"]["lastname"] = "春野"
k["Parameter"]["firstname"] = "千佳"
k["Parameter"]["nickname"] = "ちかりん"
k.save("./data/kk_chara_modified")
```

### Set Character Height to 50
```python
from kkloader import KoikatuCharaData

k = KoikatuCharaData.load("./data/kk_chara.png")
k["Custom"]["body"]["shapeValueBody"][0] = 0.5
k.save("./data/kk_chara_modified.png")  
```

### Convert Character Cards from EmotionCreators to Koikatu

[`ec_to_kk.py`](https://github.com/great-majority/KoikatuCharaLoader/blob/master/samples/ec_to_kk.py) in the sample directory might be helpful.

Using **[this web app](https://kk-snippets.streamlit.app/ec-to-kk)**, you can easily perform the conversion directly from your browser.

### Load Scene Data
The `walk()` method recursively traverses all objects including nested children (e.g., items attached to characters, objects inside folders).

```python
from kkloader import KoikatuSceneData

scene = KoikatuSceneData.load("./data/kk_scene.png")

# Simple iteration over all objects
for key, obj in scene.walk():
    obj_type = obj["type"]
    print(f"Key: {key}, Type: {obj_type}")

# With depth information (useful for visualizing hierarchy)
for key, obj, depth in scene.walk(include_depth=True):
    indent = "  " * depth
    obj_type = obj["type"]
    print(f"{indent}[depth={depth}] Key: {key}, Type: {obj_type}")

# Type-filtered iteration is also possible
for key, obj in scene.walk(object_type=KoikatuSceneData.CHARACTER):
    print(f"Character Key: {key}")
```

Object types: 0=Character, 1=Item, 2=Light, 3=Folder, 4=Route, 5=Camera, 7=Text

### Extract Character Data from Scene
You can easily extract character data using the `walk()` method above.

```python
import copy

from kkloader import KoikatuSceneData

# Load scene data
scene = KoikatuSceneData.load("./data/kk_scene.png")

# Iterate only character objects in the scene
for _, obj_info in scene.walk(object_type=KoikatuSceneData.CHARACTER):
    chara = obj_info["data"]["character"]

    # Use face thumbnail as the character card image
    chara.image = copy.deepcopy(chara.face_image)

    # Save the character data
    chara.save("./data/{}.png".format(name))
```

### Others

Various examples using this module can be found in [this repository](https://github.com/great-majority/kk-snippets), and you can also use it on [this site](https://kk-snippets.streamlit.app/).

# Contributing
*You'll need Python 3.11 and `poetry` command (you can install with `pip install poetry`).*

1. Fork the repository and pull the latest changes.
2. Run `make install` to install the dependencies.
3. Create a new branch and make changes to the code.
4. Run `make format` and `make check`
5. Once `make check` passes, push the code and open a pull request on the repository.

# Acknowledgements
- [martinwu42/pykoikatu](https://github.com/martinwu42/pykoikatu)

# Contact

[@tropical_362827](https://twitter.com/tropical_362827)
