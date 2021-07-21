# KoikatuCharaLoader
A simple deserializer / serializer for Koikatu / EmotionCreators character data.

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
>>> kc.parameter["nickname"] # Print character's nickname.
'かずのん'
>>> kc.parameter["nickname"] = "chikarin" # Renaming nickname.
>>> kc.save("./kk_chara_modified.png") # Save to `kk_chara_modified.png`.
```
that's it :)

# Export to JSON file
```
from kkloader import KoikatuCharaData

k = KoikatuCharaData.load("sa.png")
k.save_json("sa.json") 
```

`sa.json`
```sa.json
{
  "product_no": 100,
  "header": "\u3010KoiKatuChara\u3011",
  "version": "0.0.0",
  "custom": {
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

# Recipes

### Rename Character's Name
```python
from kkloader import KoikatuCharaData

k = KoikatuCharaData.load("sa.png")
k.parameter["lastname"] = "春野"
k.parameter["firstname"] = "千佳"
k.parameter["nickname"] = "ちかりん"
k.save("si.png")
```

### Set the Height of Character to 50
```python
from kkloader import KoikatuCharaData

k = KoikatuCharaData.load("sa.png")
k.custom["body"]["shapeValueBody"][0] = 0.5
k.save("si.png")  
```

### Remove Swim Cap
```python
from kkloader import KoikatuCharaData

k = KoikatuCharaData.load("sa.png")
for i,c in enumerate(k.coordinate):
    for n,p in enumerate(c["accessory"]["parts"]):
        if p["id"] == 5:
            k.coordinates[i]["accessory"]["parts"][n]["type"] = 120
k.save("si.png")  
```

### Remove Under Hair
```python
from kkloader import KoikatuCharaData
k = KoikatuCharaData.load("sa.png")
kc.Custom.body["underhairId"] = 0
k.save("si.png")
```

# Member Variables

| KoikatuCharaData.* |                  |
|-------------------:|-----------------:|
|            png_data|     raw png image|
|       face_png_data|    raw face image|
|    face, body, hair|      shape values|
|   coordinates(List)| contains seven coordinates corresponding to situation.|
| parameter | personal data (i.e. name, birthday, personality, ..etc)|

# Acknowledgements
- [martinwu42/pykoikatu](https://github.com/martinwu42/pykoikatu)