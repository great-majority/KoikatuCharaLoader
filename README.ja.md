# KoikatuCharaLoader
このプログラムは、コイカツ・エモクリ・ハニカム・サマすく・アイコミのキャラカードをPythonで読み込む・書き込むためのライブラリです。(キャラカードの他にもセーブデータ等も完全ではないですが読み込めます)

[![](https://img.shields.io/pypi/v/kkloader)](https://pypi.org/project/kkloader/)
[![Downloads](https://static.pepy.tech/badge/kkloader)](https://pepy.tech/project/kkloader)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/great-majority/KoikatuCharaLoader/blob/master/notebooks/sandbox.ja.ipynb)

# インストール
[PyPI](https://pypi.org/project/kkloader/)からインストールできます。
```
$ pip install kkloader
```
これでうまく入らないようでしたら以下のコマンドを試してみてください。
```
$ python -m pip install kkloader
```

ちょっとだけこのモジュールを試してみたい場合は、上の"Open In Colab"をクリックすることで、Colab上で実行させることもできます。

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

# 使用できるクラスの一覧

- 読み込みと書き込み両方に対応
  - `KoikatuCharaData`
  - `KoikatuSceneData`
  - `EmocreCharaData`
  - `HoneycomeCharaData`
  - `SummerVacationCharaData`
  - `SummerVacationSaveData`
  - `AicomiCharaData`
- 読み込みのみ対応
  - `KoikatuSaveData`
  - `EmocreMapData`
  - `EmocreSceneData`

いずれのクラスも `from kkloader import KoikatuCharaData` のようにインポートし、 `.load(filename)` のようにファイルを読み込むことができます。

# ブロックデータについて

コイカツのキャラデータは"ブロックデータ"というデータのかたまりから成っています。
ぞれぞれのブロックデータの中に、例えば服装の設定がまとまって入っていたり、体型の設定が入っていたりするわけです。

コイカツのキャラデータに入っているのは基本的に下記のブロックデータです。

| ブロックデータの名前 | 説明                                                         |
| -------------------- | ------------------------------------------------------------ |
| Custom               | 顔の形・体型・髪型の設定が入っています。                     |
| Coordinate           | 服装とアクセサリーの設定が入っています。                     |
| Parameter            | 名前や誕生日などの設定が入っています。                       |
| Status               | 着衣状態等の変数が入っていますが、ゲーム中にどう影響あるかは不明です。 |
| About                | 作者IDとデータIDが入っています。コイカツサンシャインから追加されています。 |
| KKEx                 | MODのデータが色々と入っているデータブロックです。            |


具体的にどのブロックデータが含まれているかは `KoikatuCharaData` クラスの `blockdata` 変数を見れば分かります。
```
>>> kc.blockdata
['Custom', 'Coordinate', 'Parameter', 'Status']
```
また、`unknown_blockdata` には未対応のフォーマットで書かれているブロックデータの名前が入っています。

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

[こちらのサイト](https://kk-snippets.streamlit.app/chara-data-viewer)にて、このプログラムによるキャラクター情報の表示をブラウザ上で試すことができます。変えたい変数を探す場合は、まずはここから目星をつけるのがよいでしょう。

![](https://i.imgur.com/E2hAdm1.png)

CLI上では `prettify` メソッドを使えば、ブロックデータに含まれている変数の一覧が見やすい形式で出力されます。
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

### KKEx内にある入れ子的なMessagePackについて

`KKEx` には、さらに内部でMessagePackでエンコードされた `bytes` 型のデータが含まれていることがあります。  
このプログラムは、`KKEx.NESTED_KEYS` に挙げられているプラグインについて追加でこのMessagePackのデータをシリアライズ/デシリアライズします。

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

### エモクリのキャラデータをコイカツのキャラデータに変換する

sampleフォルダにある [`ec_to_kk.py`](https://github.com/great-majority/KoikatuCharaLoader/blob/master/samples/ec_to_kk.py) が参考になると思います。

ただこのプログラムが使いたいだけなのであれば、**[このサイト](https://kk-snippets.streamlit.app/ec-to-kk)** から同じ処理をブラウザ上で実行することができます。

### シーンデータを読み込む
```python
from kkloader import KoikatuSceneData

scene = KoikatuSceneData.load("./data/kk_scene.png")
print(f"Version: {scene.version}")
print(f"Object count: {len(scene.dicObject)}")

# シーン内のオブジェクトを列挙
for key, obj in scene.dicObject.items():
    obj_type = obj["type"]  # 0=Character, 1=Item, 2=Light, 3=Folder
    print(f"  Key: {key}, Type: {obj_type}")

# 変更したシーンを保存
scene.save("./data/kk_scene_modified.png")
```

### その他

このモジュールを使った色々な例が [このリポジトリ](https://github.com/great-majority/kk-snippets) にあり、さらに [このサイト](https://kk-snippets.streamlit.app/) で使うこともできます。

# 開発に参加する
*Python 3.11と`poetry`コマンドが必要です(`pip install poetry`でインストールできます)。*

1. このリポジトリをフォークし、ローカルにpullします。
2. `make install`して依存関係をインストールします。
3. 新しくブランチを切り、コードに変更を加えます。
4. `make format`と`make check`を行い、変更を加えたコードをフォーマット&チェックします。
5. `make check`がエラーなく終わったなら、コードをpushしこのリポジトリにプルリクエストを出してください。

# 謝辞
- [martinwu42/pykoikatu](https://github.com/martinwu42/pykoikatu)

# 連絡先
[@tropical_362827](https://twitter.com/tropical_362827)