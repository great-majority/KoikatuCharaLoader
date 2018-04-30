# KoikatuCharaLoader
a simple deserializer / serializer for Koikatu character data.


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
    k = KoikatuCharaData("sa.png")
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
    k = KoikatuCharaData("sa.png")
    k.body["shapeValueBody"][0] = 0.5
    k.save("si.png")

if __name__=='__main__':
    main()    
```

## remove swim cap
```python
from KoikatuCharaData import KoikatuCharaData

def main():
    k = KoikatuCharaData("sa.png")
    for i,c in enumerate(k.coordinates):
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