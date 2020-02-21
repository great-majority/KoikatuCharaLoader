# KoikatuCharaLoader
a simple deserializer / serializer for Koikatu / EmotionCreators character data.

# update: "dump as json" is now available.
```
from KoikatuCharaData import KoikatuCharaData

def main():
    k = KoikatuCharaData.load("sa.png")
    k.save_json("sa.json")

if __name__=='__main__':
    main()  
```

- `sa.json`
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

# install
requires python 3.x and `msgpack`
```
$ git clone https://github.com/106-/KoikatuCharaLoader.git
$ cd KoikatuCharaLoader
$ pip install -r requirements.txt
```

# examples

## renaming character
```python
from KoikatuCharaData import KoikatuCharaData

def main():
    k = KoikatuCharaData.load("sa.png")
    k.parameter["lastname"] = "春野"
    k.parameter["firstname"] = "千佳"
    k.parameter["nickname"] = "ちかりん"
    k.save("si.png")

if __name__=='__main__':
    main()   
```

## set the height of character to 50
```python
from KoikatuCharaData import KoikatuCharaData

def main():
    k = KoikatuCharaData.load("sa.png")
    k.custom["body"]["shapeValueBody"][0] = 0.5
    k.save("si.png")

if __name__=='__main__':
    main()    
```

## remove swim cap
```python
from KoikatuCharaData import KoikatuCharaData

def main():
    k = KoikatuCharaData.load("sa.png")
    for i,c in enumerate(k.coordinate):
        for n,p in enumerate(c["accessory"]["parts"]):
            if p["id"] == 5:
                k.coordinates[i]["accessory"]["parts"][n]["type"] = 120
    k.save("si.png")

if __name__=='__main__':
    main()    
```

# member variables

| KoikatuCharaData.* |                  |
|-------------------:|-----------------:|
|            png_data|     raw png image|
|       face_png_data|    raw face image|
|    face, body, hair|      shape values|
|   coordinates(List)| contains seven coordinates corresponding to situation.|
| parameter | personal data (i.e. name, birthday, personality, ..etc)|

# refer
pngデータの長さの取得にあたり, [martinwu42/pykoikatu](https://github.com/martinwu42/pykoikatu)を参考にしました.