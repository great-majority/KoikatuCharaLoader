# KoikatuCharaLoader
A simple deserializer / serializer for Koikatu / EmotionCreators character data.

[日本語マニュアルがここにあります](README.ja.md)

# Installation
You can install this module from [PyPI](https://pypi.org/project/kkloader/).
```
$ pip install kkloader
```
If this does not work, try the following command (for Windows users, maybe).
```
$ python -m pip install kkloader
```

# Basic Usage
```python
$ python
>>> from kkloader import KoikatuCharaData # Load a module.
>>> kc = KoikatuCharaData.load("./data/kk_chara.png") # Load a character data.
>>> kc["Parameter"]["nickname"] # Print character's nickname.
'かずのん'
>>> kc["Parameter"]["nickname"] = "chikarin" # Renaming nickname.
>>> kc.save("./kk_chara_modified.png") # Save to `kk_chara_modified.png`.
```
that's it :)

# Mechanism of the Blockdata

A character data of koikatu consists of some *blockdata*.
The *blockdata* is a collection of character parameters.
A typical Koikatsu character data contains the following blockdata:

| name of blockdata | description                                                  |
| ----------------- | ------------------------------------------------------------ |
| Custom            | Values for the character's face, body, and hairstyle.        |
| Coordinate        | Values for clothes and accessories worn by characters.       |
| Parameter         | Values for character names, birthdays, preferences, etc.     |
| Status            | Values for clothed states, etc. (I'm not sure how they are used in the game) |
| About             | userID & dataID (added from Koikatu Sunshine)                |
| KKEx              | Values used in MOD                                           |

You can check which block data exists from `blockdata` in KoikatuCharaData.
```
>>> kc.blockdata
['Custom', 'Coordinate', 'Parameter', 'Status']
```
If there is block data in an unknown format, it can be checked with `unknown_blockdata`.

### Access to Blockdata
The blockdata can be accessed as a member variable of the `KoikatuCharaData` class, or accessed as a dictionary.
```python
>>> kc.Custom
<kkloader.KoikatuCharaData.Custom object at 0x7f406bf18460>
>>> kc["Custom"]
<kkloader.KoikatuCharaData.Custom object at 0x7f406bf18460>
```
So, these lines both access the same `kc.Custom`.

### Find Variables

By using the `prettify` method, the contents of the variables contained in the block of data will be displayed in an easy-to-read format.
This is useful to find which variables exists.
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
If you add `include_image=True` to the argument of `save_json`, base64-encoded images will be included in json.

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

# Contributing
*You need Python 3.9 and `poetry` command (you can install with `pip install poetry`).*

1. Fork this repository and then pull.
2. Do `make install` to install dependencies.
3. Create a new branch and make change the code.
4. Do `make format` and `make check`
5. When you passed `make check`, then push the code and make pull request on this repository.

# Acknowledgements
- [martinwu42/pykoikatu](https://github.com/martinwu42/pykoikatu)