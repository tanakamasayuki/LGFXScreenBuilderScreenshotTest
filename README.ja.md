# LGFXScreenBuilder スクリーンショットテスト

[LGFXScreenBuilder](https://github.com/tanakamasayuki/LGFXScreenBuilder) の
スクリーンショット専用リポジトリ。生成ヘッダ `Sfm.h` をヘッドレスの
`lang-ship:host` SDL バックエンドでレンダリングし、**全プロファイル × 全シーン**
の一覧を生成する。

> 📷 **出力結果（公開ギャラリー）: <https://tanakamasayuki.github.io/LGFXScreenBuilderScreenshotTest/>**

**`Sfm.h` が唯一のソース。** LGFXScreenBuilder で *「AIレイアウトを埋め込む」*
オプションを ON にしてエクスポートすると、各シーンの AI レイアウト JSON が
コメントブロックとして入る（SPEC §10.2）。コンパイル時に除去されるので実機には
影響せず、このリポジトリはヘッダだけから一覧全体を生成できる（プロジェクトファイル
不要）。意図的にキャプチャ専用で、アプリスケッチは置かない。実機で動く例は本体
リポジトリの `examples/` にある。

プロジェクトファイル `Sfm.lgfxsb.json` は一覧生成には**不要**。このサンプルでは、
サンプルの `Sfm.h` を再生成できるように置いているだけ（ツールで再エクスポート、
または codegen を実行。いずれも *AIレイアウト埋め込み* ON で）。実際に採用する側は
コミットしなくてよい — [自分のプロジェクトで使う](#自分のプロジェクトで使う) を参照。

一覧は CI で再生成され、`docs/` から GitHub Pages で公開される
（<https://tanakamasayuki.github.io/LGFXScreenBuilderScreenshotTest/>）:

- **プロファイル別**（[index.html](https://tanakamasayuki.github.io/LGFXScreenBuilderScreenshotTest/index.html)）— 各デバイスプロファイルの全シーン。
- **シーン別**（[by-scene.html](https://tanakamasayuki.github.io/LGFXScreenBuilderScreenshotTest/by-scene.html)）— シーンごとに全プロファイルを横並びにし、デバイス間のレイアウト差分を確認できる。
- 各シーンに **⧉ AI JSON** ボタンがあり、その画面のレイアウト JSON をコピーできる。
  おかしい画面はそのまま AI に貼って直せる。

## 構成

```
Sfm.h                      # 生成ヘッダ（AIレイアウト埋め込み済み）— 唯一のソース
Sfm.lgfxsb.json            # プロジェクトファイル — 一覧生成には不要。サンプルの Sfm.h 再生成用に同梱
screenshot/                # ヘッドレスキャプチャ一式
  screenshot.ino           #   全プロファイル × 全シーンを output/*.png へ描画
  sketch.yaml              #   lang-ship:host:host:mode=lgfx プロファイル
  test_screenshot.py       #   pytest-embedded ドライバ＋一覧の生成・検証
  conftest.py              #   キャプチャテスト前に output/ を消す
  gen_gallery.py           #   Sfm.h をパースして docs/ を生成（標準ライブラリのみ）
docs/                      # コミットされる一覧（GitHub Pages のソース）
  index.html / by-scene.html / ai-layouts.js
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
3. `gen_gallery.py` が `Sfm.h` の埋め込みブロックからシーン名・説明・プロファイルを
   読み取り、PNG を `docs/shots/` へ配置し、2 種類の HTML と `ai-layouts.js`
   （コピーボタン用データ）を出力する。Python 標準ライブラリのみ。Node・外部依存なし。
   `test_screenshot.py` がこれを import し、キャプチャ直後に実行するので、一覧の
   **生成と検証**（全プロファイル × 全シーンが揃っているか、各ページが空でないか）が
   同じ実行内で行われる。

## ローカル実行

`arduino-cli`・`uv`・SDL2（`sudo apt-get install -y libsdl2-dev`）が必要。
[`LGFXScreenBuilder`](https://github.com/tanakamasayuki/LGFXScreenBuilder)
ライブラリリポジトリをこのリポジトリの隣（兄弟ディレクトリ）に置くこと。
`sketch.yaml` の `dir: ../../LGFXScreenBuilder` がそれを参照する。

```bash
uv run pytest screenshot/ -v   # キャプチャ → screenshot/output/*.png、続けて docs/ を生成・検証
```

この 1 コマンドでキャプチャと一覧の再生成まで完了する。ブラウザで `docs/index.html`
を開く。**GitHub Actions は任意** — Action はこのコマンドを実行して `docs/` を
コミットし直すだけ。（既存ショットから一覧だけ作り直すには
`uv run python screenshot/gen_gallery.py`。）

## 自分のプロジェクトで使う

ハーネスは生成ヘッダ（とビルド用の LGFXScreenBuilder ライブラリ）にしか
依存しないので、どのプロジェクトにも組み込める。セットアップは一度きりで、
以降はヘッダだけを更新すればよい。

1. LGFXScreenBuilder で **「AIレイアウトを埋め込む」を ON** にしてヘッダを
   エクスポートする（ギャラリーがヘッダだけからシーン／プロファイル／レイアウトを
   読めるようにするため）。
2. ファイル一式を新しいリポジトリにコピー: 生成ヘッダ・`screenshot/`（`gen_gallery.py`
   と `conftest.py` を含む）・`pyproject.toml`・`.github/`・`.gitignore`。
   プロジェクトファイルは不要。
3. `docs/` は削除する（毎回再生成されるため）。
4. ハーネスをヘッダに合わせる: ヘッダ名を自分のものにし、
   `screenshot/screenshot.ino` の `#include "../<ヘッダ名>.h"` を一致させる。
5. push する。Action が全プロファイル × 全シーンをキャプチャし、`docs/` を
   生成してコミットして戻す。続いて Settings → Pages → **Deploy from a branch**
   → `main` / `/docs` で公開。
6. 以降は**ヘッダだけ再エクスポート**（AIレイアウト埋め込み ON）して push すれば、
   一覧が自動更新される。

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
