# KoikatuCharaLoader
このプログラムは、コイカツやエモクリのキャラカードをPythonで読み込む・書き込むためのライブラリです。(キャラカードの他にもセーブデータ等も完全ではないですが読み込めます)

# インストール
[PyPI](https://pypi.org/project/kkloader/)からインストールできます。
```
$ pip install kkloader
```
これでうまく入らないようだったら以下のコマンドを試してみてください。
```
$ python -m pip install kkloader
```

# 簡単な使い方
```python
$ python
>>> from kkloader import KoikatuCharaData # モジュールを読み込む
>>> kc = KoikatuCharaData.load("./data/kk_chara.png") # キャラデータを読み込む
>>> kc["Parameter"]["nickname"] # ニックネームを表示する
'かずのん'
>>> kc["Parameter"]["nickname"] = "ちかりん" # ニックネームを"ちかりん"にする
>>> kc.save("./kk_chara_modified.png") # `kk_chara_modified.png`へ出力する
```
簡単!

# ブロックデータについて

コイカツのキャラデータは"ブロックデータ"というデータのかたまりから成っています。
ぞれぞれのブロックデータの中に、例えば服装の設定がまとまって入っていたり、体型の設定が入っていたりするわけです。

コイカツのキャラデータに入っているのは基本的に下記のブロックデータです。

| ブロックデータの名前 | 説明                                                 |
| ----------------- | ------------------------------------------------------------ |
| Custom            | 顔の形・体型・髪型の設定が入っています。 |
| Coordinate        | 服装とアクセサリーの設定が入っています。 |
| Parameter         | 名前や誕生日などの設定が入っています。 |
| Status            | 着衣状態等の変数が入っていますが、ゲーム中にどう影響あるかは不明です。 |

具体的にどのブロックデータが含まれているかは `KoikatuCharaData` クラスの `blockdata` 変数を見れば分かります。
```
>>> kc.blockdata
['Custom', 'Coordinate', 'Parameter', 'Status']
```
また、`unknown_blockdata` には未対応のフォーマットで書かれているブロックデータの名前が入っています。
```
>>> kk_mod_chara.unknown_blockdata
['KKEx']
```
`KKEx` はMOD環境でキャラを保存したときに付くブロックデータです。ここにMODの設定値などが入っているはずです。(そのうち読めるようにするかも?)

### ブロックデータへのアクセス

ブロックデータへは `KoikatuCharaData` クラスのメンバ変数としてアクセスできる他、辞書型として読み込むこともできます。
```python
>>> kc.Custom
<kkloader.KoikatuCharaData.Custom object at 0x7f406bf18460>
>>> kc["Custom"]
<kkloader.KoikatuCharaData.Custom object at 0x7f406bf18460>
```
つまり、この2行はどちらも同じ `kc.Custom` へアクセスしています。

### 変数を探す

`prettify` メソッドを使えば、ブロックデータに含まれている変数の一覧が見やすい形式で出力されます。
これを使えば変えたい変数を探すのに便利なはずです。
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

# JSONファイルへ出力する
`save_json`メソッドを使えばキャラのデータをまとめてJSONファイルへ出力できます。
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
`save_json`メソッドの引数に `include_image=True` をつけると、base64エンコードされた画像ファイルがJSONの中に出力されます。

# 使用例

### キャラ名を変更する
```python
from kkloader import KoikatuCharaData

k = KoikatuCharaData.load("./data/kk_chara.png")
k["Parameter"]["lastname"] = "春野"
k["Parameter"]["firstname"] = "千佳"
k["Parameter"]["nickname"] = "ちかりん"
k.save("./data/kk_chara_modified")
```

### キャラの身長を50にする
```python
from kkloader import KoikatuCharaData

k = KoikatuCharaData.load("./data/kk_chara.png")
k["Custom"]["body"]["shapeValueBody"][0] = 0.5
k.save("./data/kk_chara_modified.png")  
```

### 水泳帽を削除する
```python
from kkloader import KoikatuCharaData

k = KoikatuCharaData.load("./data/kk_chara.png")
for i,c in enumerate(k["Coordinate"]):
    for n,p in enumerate(c["accessory"]["parts"]):
        if p["id"] == 5:
            k["Coordinate"][i]["accessory"]["parts"][n]["type"] = 120
k.save("./data/kk_chara_modified.png")  
```

### 陰毛を消す
```python
from kkloader import KoikatuCharaData
kc = KoikatuCharaData.load("./data/kk_chara.png")
kc["Custom"]["body"]["underhairId"] = 0
kc.save("./data/kk_chara_modified.png")
```

# 謝辞
- [martinwu42/pykoikatu](https://github.com/martinwu42/pykoikatu)