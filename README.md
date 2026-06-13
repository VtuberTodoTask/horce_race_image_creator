# 競馬配信用画像生成ツール

netkeibaの出馬表URLを入力し、配信用の馬一覧テーブル画像を生成するGUIツールです。

## 機能

- netkeibaの出馬表ページから馬データ（枠番・馬番・馬名・性齢・斤量・騎手）を自動取得
- 参加者の列を追加し、アバター画像を設定可能（ドラッグ＆ドロップ対応）
- 枠番ごとの色分け表示
- 凡例（◎本命馬・○対抗馬・●大穴・☆注目馬）付き
- PNG画像として出力

## セットアップ

```bash
pip install -r requirements.txt
```

### 日本語フォント

画像生成にはIPAゴシックなどの日本語フォントが必要です。
Ubuntu環境では以下でインストールできます:

```bash
sudo apt-get install -y fonts-ipafont-gothic
```

## 使い方

```bash
python main.py
```

1. GUIが起動します
2. netkeibaの出馬表URLを入力（例: `https://race.netkeiba.com/race/shutuba.html?race_id=202605030211`）
3. 参加者数を設定し、名前やアバター画像を任意で設定
4. 「画像を生成」ボタンをクリック
5. 指定した場所にPNG画像が出力されます

## exeファイルの作成

Python環境がなくても実行できるexeファイルを作成できます。

```bash
pip install -r requirements.txt
python build_exe.py
```

ビルド完了後、`dist/HorceRaceImageCreator/` フォルダ内に実行ファイルが生成されます。
このフォルダごと配布すればPython環境なしで利用できます。

## ファイル構成

- `main.py` - GUIアプリケーション（tkinter）
- `scraper.py` - netkeibaスクレイピングモジュール
- `image_generator.py` - 画像生成モジュール（Pillow）
- `settings.py` - 設定の保存/読込モジュール
- `build_exe.py` - exe作成スクリプト（PyInstaller）
- `requirements.txt` - Python依存パッケージ
