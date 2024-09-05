# KoikatuCharaLoader
A simple deserializer and serializer for character data from Koikatu, EmotionCreators, Honeycome, and SummerVacationScramble.

[![](https://img.shields.io/pypi/v/kkloader)](https://pypi.org/project/kkloader/)
[![Downloads](https://static.pepy.tech/badge/kkloader)](https://pepy.tech/project/kkloader)

[日本語マニュアルがここにあります](README.ja.md)

# Installation
You can install the module from [PyPI](https://pypi.org/project/kkloader/).
```
$ pip install kkloader
```
If this doesn't work, try the following command (this may be for Windows users).
```
$ python -m pip install kkloader
```

# Basic Usage
```python
$ python
>>> from kkloader import KoikatuCharaData # Load the module.
>>> kc = KoikatuCharaData.load("./data/kk_chara.png") # Load character data.
>>> kc["Parameter"]["nickname"] # Print the character's nickname.
'かずのん'
>>> kc["Parameter"]["nickname"] = "chikarin" # Rename the nickname.
>>> kc.save("./kk_chara_modified.png") # Save to `kk_chara_modified.png`.
```
That's it! :)

# List of Classes

- Supports saving and loading:
  - `KoikatuCharaData`
  - `EmocreCharaData`
  - `HoneycomeCharaData`
  - `SummerVacationCharaData`
  - `SummerVacationSaveData`
- Supports loading only:
  - `KoikatuSaveData`
  - `EmocreMapData`
  - `EmocreSceneData`

Any class can be imported with `from kkloader import KoikatuCharaData` and data can be loaded using the `.load(filename)` method.

# Mechanism of the Blockdata

Koikatu character data consists of several *block data* sections. Each *block data* contains various character parameters. A typical Koikatsu character data includes the following block data:

| name of blockdata | description                                                  |
| ----------------- | ------------------------------------------------------------ |
| Custom            | Values for the character's face, body, and hairstyle.        |
| Coordinate        | Values for clothes and accessories worn by characters.       |
| Parameter         | Values for character's name, birthday, preferences, etc.     |
| Status            | Values for clothed states, etc. (Usage in the game is unclear) |
| About             | userID & dataID (added from Koikatu Sunshine)                |
| KKEx              | Values used in MOD                                           |

You can check which block data is present in `blockdata` from the `KoikatuCharaData` object:
```
>>> kc.blockdata
['Custom', 'Coordinate', 'Parameter', 'Status']
```
If there is block data in an unknown format, it can be found using `unknown_blockdata`.

### Access to Blockdata
The block data can be accessed either as a member variable of the `KoikatuCharaData` class or as a dictionary.
```python
>>> kc.Custom
<kkloader.KoikatuCharaData.Custom object at 0x7f406bf18460>
>>> kc["Custom"]
<kkloader.KoikatuCharaData.Custom object at 0x7f406bf18460>
```
As shown, both lines access the same `kc.Custom`.

### Find Variables

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

# Export to JSON file
```
from kkloader import KoikatuCharaData

k = KoikatuCharaData.load("./data/kk_chara.png")
k.save_json("data.json") 
```

`data.json`
```data.json
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

### Rename Character's Name
```python
from kkloader import KoikatuCharaData

k = KoikatuCharaData.load("./data/kk_chara.png")
k["Parameter"]["lastname"] = "春野"
k["Parameter"]["firstname"] = "千佳"
k["Parameter"]["nickname"] = "ちかりん"
k.save("./data/kk_chara_modified")
```

### Set the Height of Character to 50
```python
from kkloader import KoikatuCharaData

k = KoikatuCharaData.load("./data/kk_chara.png")
k["Custom"]["body"]["shapeValueBody"][0] = 0.5
k.save("./data/kk_chara_modified.png")  
```

### Remove Swim Cap
```python
from kkloader import KoikatuCharaData

k = KoikatuCharaData.load("./data/kk_chara.png")
for i,c in enumerate(k["Coordinate"]):
    for n,p in enumerate(c["accessory"]["parts"]):
        if p["id"] == 5:
            k["Coordinate"][i]["accessory"]["parts"][n]["type"] = 120
k.save("./data/kk_chara_modified.png")  
```

### Remove Under Hair
```python
from kkloader import KoikatuCharaData
kc = KoikatuCharaData.load("./data/kk_chara.png")
kc["Custom"]["body"]["underhairId"] = 0
kc.save("./data/kk_chara_modified.png")
```

### Convert Character Cards from EmotionCreators to Koikatu

[`ec_to_kk.py`](https://github.com/great-majority/KoikatuCharaLoader/blob/master/samples/ec_to_kk.py) in the sample directory might be helpful.

Using **[this web app](https://kk-snippets.streamlit.app/ec-to-kk)**, you can easily perform the conversion directly from your browser.

### Others

Various examples using this module can be found in [this repository](https://github.com/great-majority/kk-snippets), and you can also use it on [this site](https://kk-snippets.streamlit.app/).

# Contributing
*You'll need Python 3.11 and `poetry` command (you can install with `pip install poetry`).*

1. Fork the repository and pull the latest changes.
2. Run `make install` to install the dependencies.
3. Create a new branch and make changes the code.
4. Run `make format` and `make check`
5. Once `make check` passes, push the code and open a pull request on the repository.

# Acknowledgements
- [martinwu42/pykoikatu](https://github.com/martinwu42/pykoikatu)

# Contact

[@tropical_362827](https://twitter.com/tropical_362827)
