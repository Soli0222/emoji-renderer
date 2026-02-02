# Emoji Renderer Service - 実装結果仕様書

## 1. 概要

**サービス名:** Emoji Renderer Service  
**バージョン:** 1.0.0  
**責務:** Misskey Custom Emoji用のテキスト画像生成（レンダリング）マイクロサービス  
**出力形式:** 静止画 WebP / アニメーション APNG

---

## 2. 技術スタック

| カテゴリ | 採用技術 | バージョン |
|---------|---------|-----------|
| Runtime | Python | 3.13+ |
| Web Framework | FastAPI | 0.115.0 |
| ASGI Server | Uvicorn | 0.30.6 |
| 画像処理 | Pillow (PIL) | 10.4.0 |
| 数値計算 | NumPy | 2.1.1 |
| 設定管理 | pydantic-settings | 2.5.2 |
| メトリクス | prometheus-client | 0.21.0 |
| ロギング | python-json-logger | 2.0.7 |

---

## 3. ディレクトリ構造

```
emoji-renderer/
├── main.py                 # アプリケーションエントリーポイント
├── requirements.txt        # Python依存パッケージ
├── Dockerfile              # コンテナビルド定義
├── .env.example            # 環境変数サンプル
├── .gitignore
├── README.md
├── assets/
│   └── fonts/              # TTFフォントファイル (161ファイル)
├── docs/
│   ├── openapi.yaml        # OpenAPI仕様
│   ├── spec.md             # 設計仕様書
│   └── result.md           # 本ドキュメント
└── src/
    ├── __init__.py
    ├── config.py           # 環境変数ベースの設定
    ├── api/
    │   ├── __init__.py
    │   ├── routes.py       # APIエンドポイント定義
    │   └── schemas.py      # Pydanticスキーマ
    ├── core/
    │   ├── __init__.py
    │   ├── engine.py       # レンダリングオーケストレーター
    │   ├── text.py         # テキスト描画処理
    │   ├── animation.py    # アニメーション生成
    │   └── fonts.py        # フォント管理
    └── utils/
        ├── __init__.py
        └── color.py        # 色変換ユーティリティ
```

---

## 4. API エンドポイント

### 4.1. ヘルスチェック

```
GET /health
```

**レスポンス:**
```json
{"status": "ok"}
```

---

### 4.2. フォント一覧取得

```
GET /fonts
```

**レスポンス例:**
```json
[
  {
    "id": "notosansjp_black",
    "name": "Notosansjp Black",
    "categories": ["sans-serif"]
  },
  {
    "id": "zenmarugothic_bold",
    "name": "Zenmarugothic Bold",
    "categories": ["sans-serif"]
  }
]
```

**登録フォント数:** 161フォント

---

### 4.3. 画像生成

```
POST /generate
Content-Type: application/json
```

**リクエストボディ:**

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| `text` | string | ✅ | - | レンダリングするテキスト（最大20文字、改行`\n`対応） |
| `layout.mode` | string | - | `"square"` | `"square"`: 256×256固定 / `"banner"`: 高さ256、幅可変 |
| `layout.alignment` | string | - | `"center"` | `"left"` / `"center"` / `"right"` |
| `style.fontId` | string | ✅ | - | `/fonts`で取得したフォントID |
| `style.textColor` | string | ✅ | - | テキスト色（HEX形式: `#RRGGBB`） |
| `style.outlineColor` | string | - | `"#FFFFFF"` | アウトライン色 |
| `style.outlineWidth` | integer | - | `0` | アウトライン幅（0-20px） |
| `style.shadow` | boolean | - | `false` | ドロップシャドウ有効化 |
| `motion.type` | string | - | `"none"` | `"none"` / `"shake"` / `"spin"` / `"bounce"` / `"gaming"` |
| `motion.intensity` | string | - | `"medium"` | `"low"` / `"medium"` / `"high"` |

**レスポンス:**
- 静止画: `image/webp`
- アニメーション: `image/apng`

---

## 5. リクエスト例

### 5.1. シンプルな静止画

```bash
curl -X POST http://localhost:8109/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "草",
    "style": {
      "fontId": "notosansjp_black",
      "textColor": "#00FF00"
    }
  }' \
  --output emoji.webp
```

### 5.2. アウトライン付き（複数行）

```bash
curl -X POST http://localhost:8109/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "進捗\nどう？",
    "style": {
      "fontId": "mplus1_black",
      "textColor": "#FF0000",
      "outlineColor": "#FFFFFF",
      "outlineWidth": 5
    }
  }' \
  --output outline.webp
```

### 5.3. シェイクアニメーション

```bash
curl -X POST http://localhost:8109/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "ﾌﾞﾙﾌﾞﾙ",
    "style": {
      "fontId": "mplusrounded1c_bold",
      "textColor": "#3366FF"
    },
    "motion": {
      "type": "shake",
      "intensity": "high"
    }
  }' \
  --output shake.apng
```

### 5.4. ゲーミング（虹色回転）

```bash
curl -X POST http://localhost:8109/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "GAMING",
    "style": {
      "fontId": "notosansjp_black",
      "textColor": "#FF0000",
      "outlineColor": "#000000",
      "outlineWidth": 3
    },
    "motion": {
      "type": "gaming",
      "intensity": "high"
    }
  }' \
  --output gaming.apng
```

### 5.5. スピン（回転）

```bash
curl -X POST http://localhost:8109/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "回転",
    "style": {
      "fontId": "zenmarugothic_black",
      "textColor": "#9933FF"
    },
    "motion": {
      "type": "spin",
      "intensity": "medium"
    }
  }' \
  --output spin.apng
```

### 5.6. バウンス（跳ね）

```bash
curl -X POST http://localhost:8109/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "ぴょん",
    "style": {
      "fontId": "hachimarupop_regular",
      "textColor": "#FF6699"
    },
    "motion": {
      "type": "bounce",
      "intensity": "high"
    }
  }' \
  --output bounce.apng
```

---

## 6. 利用可能フォント（抜粋）

### ゴシック系（太字）
| ID | 名称 |
|----|------|
| `notosansjp_black` | Noto Sans JP Black |
| `notosansjp_bold` | Noto Sans JP Bold |
| `mplus1_black` | M PLUS 1 Black |
| `mplus2_black` | M PLUS 2 Black |
| `bizudgothic_bold` | BIZ UD Gothic Bold |

### 丸ゴシック系
| ID | 名称 |
|----|------|
| `zenmarugothic_black` | Zen Maru Gothic Black |
| `mplusrounded1c_bold` | M PLUS Rounded 1c Bold |
| `kiwimaru_medium` | Kiwi Maru Medium |

### ポップ・かわいい系
| ID | 名称 |
|----|------|
| `hachimarupop_regular` | はちまるポップ |
| `mochiypopone_regular` | もちポップ One |
| `mochiypoppone_regular` | もちポップ P One |

### 明朝体
| ID | 名称 |
|----|------|
| `notoserifjp_bold` | Noto Serif JP Bold |
| `shipporimincho_bold` | しっぽり明朝 Bold |
| `zenoldmincho_bold` | Zen Old Mincho Bold |

### 個性派・デザイン系
| ID | 名称 |
|----|------|
| `reggaeone_regular` | レゲエ One |
| `rocknrollone_regular` | ロックンロール One |
| `delagothicone_regular` | デラゴシック One |
| `rampartone_regular` | ランパート One |
| `stick_regular` | Stick |

---

## 7. 環境変数

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `LOG_LEVEL` | `INFO` | ログレベル（DEBUG/INFO/WARNING/ERROR） |
| `MAX_TEXT_LENGTH` | `20` | 入力テキスト最大文字数 |
| `MAX_IMAGE_SIZE_KB` | `1024` | 出力画像サイズ上限（KB） |
| `DEFAULT_FONT_ID` | `noto_sans_jp_bold` | デフォルトフォントID |
| `FONT_DIRECTORY` | `./assets/fonts` | フォントディレクトリパス |
| `HOST` | `0.0.0.0` | サーバーバインドアドレス |
| `PORT` | `8109` | アプリケーションポート |
| `METRICS_PORT` | `9109` | Prometheusメトリクスポート |

---

## 8. メトリクス

**エンドポイント:** `http://localhost:9109/metrics`

| メトリクス名 | 型 | 説明 |
|-------------|-----|------|
| `render_duration_seconds` | Histogram | レンダリング処理時間 |
| `render_requests_total` | Counter | リクエスト総数 |
| `render_errors_total` | Counter | エラー発生数 |

---

## 9. エラーレスポンス

| HTTPステータス | 発生条件 |
|---------------|---------|
| `400 Bad Request` | 出力画像サイズが上限超過 |
| `422 Validation Error` | 不正なカラーコード、存在しないfontId、テキスト長超過 |
| `500 Internal Server Error` | レンダリング処理中の予期せぬ例外 |

---

## 10. 起動方法

### ローカル開発

```bash
# 仮想環境作成・有効化
python -m venv venv
source venv/bin/activate

# 依存パッケージインストール
pip install -r requirements.txt

# サーバー起動
python main.py
```

### Docker

```bash
# ビルド（161フォントはSIL OFLライセンスでイメージに同梱）
docker build -t emoji-renderer .

# 起動（アプリ: 8109、メトリクス: 9109）
docker run -p 8109:8109 -p 9109:9109 emoji-renderer
```

---

## 11. 実装状況サマリ

| 仕様項目 | 状態 | 備考 |
|---------|------|------|
| FastAPI Webフレームワーク | ✅ 完了 | |
| `/health` エンドポイント | ✅ 完了 | |
| `/fonts` エンドポイント | ✅ 完了 | 161フォント登録済み |
| `/generate` エンドポイント | ✅ 完了 | |
| Square モード (256×256) | ✅ 完了 | デフォルト |
| Banner モード (幅可変) | ✅ 完了 | |
| フォントサイズ自動計算 | ✅ 完了 | 二分探索アルゴリズム |
| 袋文字（アウトライン） | ✅ 完了 | stroke_width使用 |
| ドロップシャドウ | ✅ 完了 | ガウシアンブラー適用 |
| Shake アニメーション | ✅ 完了 | |
| Spin アニメーション | ✅ 完了 | |
| Bounce アニメーション | ✅ 完了 | |
| Gaming（虹色）アニメーション | ✅ 完了 | HSL色相回転 |
| WebP 静止画出力 | ✅ 完了 | |
| APNG アニメーション出力 | ✅ 完了 | |
| Prometheus メトリクス | ✅ 完了 | 別ポート(9109) |
| JSON ロギング | ✅ 完了 | python-json-logger |
| 環境変数設定 | ✅ 完了 | pydantic-settings |
| Dockerfile | ✅ 完了 | Python 3.13 Alpine、フォント同梱 |
| 入力バリデーション | ✅ 完了 | Pydantic |
| エラーハンドリング | ✅ 完了 | 400/422/500 |

---

## 12. 今後の拡張案

- [ ] フォントカテゴリの自動分類精度向上
- [ ] カスタムフォントアップロード機能
- [ ] 出力サイズ指定オプション（128×128, 512×512等）
- [ ] グラデーション塗りつぶし
- [ ] 縁取りの二重化（多重アウトライン）
- [ ] キャッシュ機構（同一リクエストの再利用）
