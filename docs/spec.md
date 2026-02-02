# Service A: Emoji Renderer - 詳細実装仕様書 (v1.0)

## 1. 概要

**責務:** Misskey Custom Emoji用の画像生成（レンダリング）に特化したマイクロサービス。
**特性:** ステートレス、CPUバウンド、決定論的（Deterministic）。
**入力:** テキスト、スタイル設定、アニメーション設定を含むJSON。
**出力:** 画像バイナリ（静止画WebP または 動画APNG）。

## 2. 技術スタック & 環境

* **Runtime:** Python 3.11+
* **Web Framework:** FastAPI
* **Server Interface:** Uvicorn (ASGI)
* **Image Processing:**
* **Pillow (PIL):** メインの描画、合成、WebP/APNG書き出し。
* **NumPy:** 高速なピクセル操作（特にGaming Modeの色相回転処理などで使用推奨）。


* **Container:** `python:3.14.2-alpine3.23` ベース（軽量化のため）。

## 3. モジュールアーキテクチャ

内部を3層構造に分離し、ロジックの独立性を担保する。

```text
src/
├── api/             # Interface Layer (FastAPI)
│   ├── routes.py    # エンドポイント定義 (/generate, /fonts)
│   └── schemas.py   # Pydanticモデル (Request/Response定義)
├── core/            # Business Logic Layer (Rendering Engine)
│   ├── engine.py    # 描画パイプラインのオーケストレーター
│   ├── text.py      # 文字の描画、フォントサイズ計算、袋文字処理
│   ├── animation.py # フレームごとの変形ロジック (Shake, Spin, etc.)
│   └── fonts.py     # フォントファイルの読み込み・管理
└── utils/           # Shared Utilities
    └── color.py     # HEX <-> RGB <-> HSL 変換

```

## 4. コアロジック仕様

### 4.1. フォント管理 (`core/fonts.py`)

* **初期化:** 起動時に指定ディレクトリ（例: `./assets/fonts/`）をスキャンする。
* **マッピング:** ファイル名またはメタデータから一意なID（`fontId`）を生成し、メモリ上に辞書として保持する。
* **フォールバック:** リクエストされた `fontId` が存在しない場合、デフォルトフォント（例: Noto Sans JP Bold）を使用せず、**エラー(422)を返す**（AI側のハルシネーション検知のため厳格にする）。

### 4.2. テキスト描画パイプライン (`core/text.py`)

1. **Canvas作成:** 指定された `width`, `height` のRGBAモードのCanvasを作成。
2. **フォントサイズ計算:**
* **Banner Mode:** 指定フォントサイズ（デフォルト固定）を使用。Canvas幅は文字幅に合わせて拡張。
* **Square Mode:** 256x256px の枠内に収まる最大フォントサイズを算出する。
* *アルゴリズム:* 二分探索、またはダミー描画によるループで `bbox` が枠内に収まる最大値を探索する。




3. **ベース描画:**
* テキストを中央揃えで描画。
* **袋文字 (Outline):** Pillowの `stroke_width` を使用。
* *品質向上:* 標準のstrokeが汚い場合は、テキストを8方向（上下左右斜め）にずらして描画する古典的な手法、または画像処理的なDilation（膨張）処理を検討。今回はPillow標準の機能で可とする。


* **影 (Shadow):** ドロップシャドウが有効な場合、ガウシアンブラーをかけた黒いレイヤーを背面に合成する。



### 4.3. アニメーション生成パイプライン (`core/animation.py`)

静止画（WebP）の場合はベース画像をそのまま出力。モーション指定がある場合は以下のフローを実行。

**共通設定:**

* **Frame Rate:** 20 fps (0.05s/frame) を基準とする。
* **Duration:** ループ一周分の長さ（例: 1.0秒 = 20フレーム）。

**モーション別ロジック:**

| モーション | ロジック詳細 |
| --- | --- |
| **Shake** (振動) | 各フレームでランダムな `(dx, dy)` を生成し、Canvas全体をずらす。`intensity` で振れ幅（px）を調整。前のフレームの残像が残らないよう、毎回クリアして描画。 |
| **Spin** (回転) | 画像中心を軸にアフィン変換で回転させる。`speed` で1周にかかるフレーム数を制御。 |
| **Bounce** (跳ね) | Y軸座標に対し、サイン波 `y = sin(t) * amp` を適用して上下させる。接地感（潰れる表現）は今回は不要とする。 |
| **Gaming** (七色) | テキストの塗りつぶし色をフレームごとにHSL色空間で回転させ、RGBに戻して再描画する。**注意:** 背景やアウトラインの色は維持すること。 |

**APNGエンコード:**

* Pillowの `image.save(fp, format='PNG', save_all=True, append_images=frames, duration=ms, loop=0)` を使用。
* ファイルサイズ削減のため、最適化オプション（`optimize=True`）を有効化する。

## 5. エラーハンドリング & バリデーション

FastAPI/Pydantic層で厳格に弾く。

* **400 Bad Request:**
* 画像生成の結果、ファイルサイズがMisskeyの制限（例えば500KB〜1MBなど、環境変数で設定）を超過した場合。


* **422 Validation Error:**
* Colorコードが不正 (`#ZZZ` など)。
* `text` が空、または長すぎる（上限20文字）。
* `fontId` がシステムに存在しない。


* **500 Internal Server Error:**
* 描画処理中の予期せぬ例外。Stacktraceはログに出力し、レスポンスには含めない。



## 6. インフラ・運用設計

### 6.1. Dockerfile 設計

* ベースイメージ: `python:3.14.2-alpine3.23`
* 依存パッケージ:
* システム: `fonts-noto-cjk` (デフォルト用), `libwebp-dev`
* Python: `requirements.txt`


* アセット:
* `./assets/fonts/` をコンテナにCOPY、またはVolumeマウントできるようにする。



### 6.2. 環境変数 (Configuration)

`k8s ConfigMap` からの注入を想定。

```bash
LOG_LEVEL=INFO           # debug, info, warning, error
MAX_TEXT_LENGTH=20       # 入力文字数制限
MAX_IMAGE_SIZE_KB=1024   # 出力バイナリのソフトリミット
DEFAULT_FONT_ID=noto_sans_jp_bold

```

### 6.3. Observability

* **Logging:** JSON形式で標準出力へ（lokiでの回収を想定）。
* Log fields: `requestId`, `latency_ms`, `output_format`, `output_size_bytes`


* **Metrics:** `/metrics` エンドポイント (Prometheus形式)
* `render_duration_seconds`: ヒストグラム。描画にかかった時間。
* `render_errors_total`: カウンター。エラー発生数。
