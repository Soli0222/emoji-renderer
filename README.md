# Emoji Renderer Service

Misskey Custom Emoji用の画像生成（レンダリング）に特化したマイクロサービス。

## 機能

- テキストから静止画（WebP）またはアニメーション（APNG）を生成
- 複数のフォントサポート
- 袋文字（アウトライン）、影などのスタイリング
- アニメーション効果: Shake, Spin, Bounce, Gaming（七色）

## 技術スタック

- Python 3.13+
- FastAPI 0.115.0
- Pillow (PIL) 10.4.0
- NumPy 2.1.1
- prometheus-client 0.21.0
- pydantic-settings 2.5.2

## セットアップ

### ローカル開発

```bash
# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# 依存関係のインストール
pip install -r requirements.txt

# フォントディレクトリの作成
mkdir -p assets/fonts

# フォントファイルを assets/fonts/ に配置

# サーバーの起動
python main.py
```

### Docker

```bash
# イメージのビルド（フォントはSIL OFLライセンスでイメージに含まれます）
docker build -t emoji-renderer .

# コンテナの実行（アプリ: 8109、メトリクス: 9109）
docker run -p 8109:8109 -p 9109:9109 emoji-renderer
```

## API エンドポイント

### Health Check

```
GET /health
```

### フォント一覧

```
GET /fonts
```

### 画像生成

```
POST /generate
Content-Type: application/json

{
  "text": "進捗\nどう？",
  "layout": {
    "mode": "square",
    "alignment": "center"
  },
  "style": {
    "fontId": "noto_sans_jp_black",
    "textColor": "#FF0000",
    "outlineColor": "#FFFFFF",
    "outlineWidth": 5,
    "shadow": true
  },
  "motion": {
    "type": "shake",
    "intensity": "medium",
    "speed": 1.0
  }
}
```

### Prometheus メトリクス（ポート9109）

```
GET http://localhost:9109/metrics
```

## 環境変数

| 変数名 | デフォルト | 説明 |
|--------|------------|------|
| `LOG_LEVEL` | `INFO` | ログレベル (debug, info, warning, error) |
| `MAX_TEXT_LENGTH` | `20` | 入力文字数制限 |
| `MAX_IMAGE_SIZE_KB` | `1024` | 出力画像サイズ制限 (KB) |
| `DEFAULT_FONT_ID` | `noto_sans_jp_bold` | デフォルトフォントID |
| `FONT_DIRECTORY` | `./assets/fonts` | フォントディレクトリパス |
| `HOST` | `0.0.0.0` | サーバーホスト |
| `PORT` | `8109` | アプリケーションポート |
| `METRICS_PORT` | `9109` | Prometheusメトリクスポート |

## ディレクトリ構造

```
src/
├── api/             # Interface Layer (FastAPI)
│   ├── routes.py    # エンドポイント定義
│   └── schemas.py   # Pydanticモデル
├── core/            # Business Logic Layer
│   ├── engine.py    # 描画パイプラインのオーケストレーター
│   ├── text.py      # テキスト描画処理
│   ├── animation.py # アニメーション生成
│   └── fonts.py     # フォント管理
└── utils/           # Shared Utilities
    └── color.py     # 色変換ユーティリティ
```

## License

MIT
