# KoikatuCharaLoader
a simple deserializer / serializer for Koikatu character data.


# install
requires python 3.x.
```
$ git clone https://github.com/106-/KoikatuCharaLoader.git
$ cd KoikatuCharaLoader
$ pip install -r requirements.txt
```

# examples

## renaming character
```
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
```
from KoikatuCharaData import KoikatuCharaData

def main():
    k = KoikatuCharaData("sa.png")
    k.body["shapeValueBody"][0] = 0.5
    k.save("si.png")

if __name__=='__main__':
    main()    
```