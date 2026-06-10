# LGFXScreenBuilder スクリーンショットテスト

[LGFXScreenBuilder](https://github.com/tanakamasayuki/LGFXScreenBuilder) の
スクリーンショット専用リポジトリ。画面定義（`Sfm.lgfxsb.json` → `Sfm.h`）を
ヘッドレスの `lang-ship:host` SDL バックエンドでレンダリングし、
**全プロファイル × 全シーン**の一覧を生成する。

意図的にキャプチャ専用で、アプリスケッチは置かない。重要なのはプロジェクト定義と
その生成ヘッダの 2 ファイルだけ。実機で動く例は本体リポジトリの `examples/` にある。

一覧は CI で再生成され、`docs/` から GitHub Pages で公開される:

- **プロファイル別**（`docs/index.html`）— 各デバイスプロファイルの全シーン。
- **シーン別**（`docs/by-scene.html`）— シーンごとに全プロファイルを横並びにし、
  デバイス間のレイアウト差分を確認できる。

## 構成

```
Sfm.lgfxsb.json            # プロジェクト定義（プロファイル＋シーン）— ソース
Sfm.h                      # 生成ヘッダ — キャプチャの唯一の実入力
screenshot/                # ヘッドレスキャプチャ一式
  screenshot.ino           #   全プロファイル × 全シーンを output/*.png へ描画
  sketch.yaml              #   lang-ship:host:host:mode=lgfx プロファイル
  test_screenshot.py       #   pytest-embedded ドライバ
gen_gallery.py             # キャプチャ済み PNG から docs/ を生成（標準ライブラリのみ）
docs/                      # コミットされる一覧（GitHub Pages のソース）
  shots/<profile>/<scene>.png
```

## 仕組み

1. `screenshot.ino` が生成ヘッダ `../Sfm.h` を取り込み、各プロファイルの
   ネイティブ解像度でオフスクリーン `LGFX` デバイスを生成し、
   `screen.show(sceneId)`（デザイン／プレビュー状態）を呼び、`createPng()` で
   フレームバッファを `output/<profile>__<scene>.png` に書き出す。
   物理ボードに依存せず 1 回の実行で全組み合わせをキャプチャする。
2. `test_screenshot.py` が
   [pytest-embedded-arduino-cli](https://github.com/tanakamasayuki/pytest-embedded-arduino-cli)
   経由でスケッチをビルドし、ヘッドレス `mode=lgfx`（SDL dummy ドライバ）で駆動する。
3. `gen_gallery.py` が PNG を `docs/shots/` へ配置し、2 種類の静的 HTML を出力する。
   Python 標準ライブラリのみ。Node・外部依存なし。

## ローカル実行

`arduino-cli`・`uv`・SDL2（`sudo apt-get install -y libsdl2-dev`）が必要。
[`LGFXScreenBuilder`](https://github.com/tanakamasayuki/LGFXScreenBuilder)
ライブラリリポジトリをこのリポジトリの隣（兄弟ディレクトリ）に置くこと。
`sketch.yaml` の `dir: ../../LGFXScreenBuilder` がそれを参照する。

```bash
uv run pytest screenshot/ -v   # キャプチャ → screenshot/output/*.png
python3 gen_gallery.py         # 一覧生成 → docs/
```

ブラウザで `docs/index.html` を開く。**GitHub Actions は任意** — Action はこの
2 コマンドを自動化しているだけ。

## 自分のプロジェクトで使う

ハーネスは生成ヘッダと LGFXScreenBuilder ライブラリにしか依存しないので、
どのプロジェクトにも組み込める。セットアップは一度きりで、以降はヘッダだけを
更新すればよい。

1. ファイル一式を新しいリポジトリにコピー: `*.lgfxsb.json`・生成ヘッダ・
   `screenshot/`・`gen_gallery.py`・`conftest.py`・`pyproject.toml`・
   `.github/`・`.gitignore`。
2. `docs/` は削除する（毎回再生成されるため）。
3. ハーネスをヘッダに合わせる: ヘッダ名を自分のものにし、
   `screenshot/screenshot.ino` の `#include "../<ヘッダ名>.h"` を一致させる
   （include 名は生成 `.h` と揃えること）。
4. push する。Action が全プロファイル × 全シーンをキャプチャし、`docs/` を
   生成してコミットして戻す。
5. Settings → Pages → **Deploy from a branch** → `main` / `/docs` で公開。
6. 以降は LGFXScreenBuilder で**ヘッダだけ再生成**して push すれば、一覧が
   自動更新される。

### 画像の置き場所

コミットした PNG は `.git` を徐々に肥大化させる。**画面キャプチャ専用リポジトリ
（これ）を推奨**し、アプリ本体リポジトリの履歴に画像を入れないようにする。

どうしても既存のアプリリポジトリ内でキャプチャする場合は、`docs/shots/` を
ブランチにコミットせず一覧を隔離する: `docs/` を Pages の deploy **アーティファクト**
（`actions/deploy-pages`）経由で公開するか、外部ストレージへ送る。定期的な履歴の
squash（圧縮）も有効。

> このサンプルは意図的に最小限。リポジトリを小さく保つため履歴を squash しても構わない。

## CI

`.github/workflows/screenshots.yml` は、プロジェクトまたはハーネスに触れる
push（および手動実行）で動作する。本リポジトリとライブラリリポジトリを兄弟として
チェックアウトし、キャプチャ → `docs/` 再生成 → 一覧をコミットして戻す。
