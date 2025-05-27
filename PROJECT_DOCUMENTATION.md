# CSV Query Agent Documentation

## プロジェクト概要

CSV Query Agentは、アップロードされたCSVファイルに対して自然言語で質問できるWebアプリケーションです。Next.js（App Router）をフロントエンドに、PythonとOpenAI Agent SDKをバックエンドに使用して構築されています。

### 主な機能

- CSVファイルのアップロード
- 自然言語でのデータクエリ
- AIによる自動データ分析と可視化
- リアルタイムレスポンス
- セッション管理とクエリ履歴

## システムアーキテクチャ

### 技術スタック

#### フロントエンド
- **Next.js 14+** (App Router)
- **TypeScript**
- **Tailwind CSS** (スタイリング)
- **React Query** (データフェッチング)
- **Shadcn/ui** (UIコンポーネント)

#### バックエンド
- **Python 3.11+**
- **FastAPI** (Webフレームワーク)
- **OpenAI Agent SDK** (AI処理)
- **Pandas** (データ処理)
- **Uvicorn** (ASGIサーバー)

### アーキテクチャ図

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Next.js App    │────▶│  Python API     │────▶│  OpenAI API     │
│  (Frontend)     │     │  (FastAPI)      │     │                 │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │
        │                       │
        ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │
│  File Storage   │     │  Session Store  │
│  (Uploads)      │     │  (Redis/Memory) │
│                 │     │                 │
└─────────────────┘     └─────────────────┘
```

## API仕様

### エンドポイント

#### 1. ファイルアップロード
```
POST /api/upload
Content-Type: multipart/form-data

Request:
- file: CSVファイル (max 10MB)

Response:
{
  "session_id": "uuid",
  "file_name": "data.csv",
  "columns": ["col1", "col2", ...],
  "row_count": 1000,
  "preview": [...] // 最初の5行
}
```

#### 2. クエリ実行
```
POST /api/query
Content-Type: application/json

Request:
{
  "session_id": "uuid",
  "query": "売上が最も高い月は？"
}

Response:
{
  "answer": "最も売上が高いのは12月で、売上額は¥1,234,567です。",
  "data": {...},
  "visualization": {
    "type": "bar_chart",
    "data": {...}
  },
  "sql_query": "SELECT month, SUM(sales) FROM data GROUP BY month ORDER BY SUM(sales) DESC LIMIT 1"
}
```

#### 3. セッション履歴
```
GET /api/sessions/{session_id}/history

Response:
{
  "queries": [
    {
      "id": "query_id",
      "query": "...",
      "answer": "...",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ]
}
```

## フロントエンド実装

### ディレクトリ構造
```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── api/
│   │   └── [...route handlers]
│   └── components/
│       ├── FileUploader.tsx
│       ├── QueryInput.tsx
│       ├── ResultDisplay.tsx
│       └── VisualizationChart.tsx
├── lib/
│   ├── api-client.ts
│   └── utils.ts
├── hooks/
│   ├── useQuery.ts
│   └── useFileUpload.ts
└── types/
    └── index.ts
```

### 主要コンポーネント

#### FileUploader
```typescript
interface FileUploaderProps {
  onUploadComplete: (sessionId: string) => void;
}
```

#### QueryInput
```typescript
interface QueryInputProps {
  sessionId: string;
  onQuerySubmit: (query: string) => void;
}
```

## バックエンド実装

### ディレクトリ構造
```
backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── upload.py
│   │   ├── query.py
│   │   └── session.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── csv_agent.py
│   │   └── tools.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   └── services/
│       ├── __init__.py
│       ├── file_service.py
│       └── session_service.py
├── requirements.txt
└── config.py
```

### OpenAI Agent実装

```python
from openai import OpenAI
from swarm import Swarm, Agent

class CSVQueryAgent:
    def __init__(self, csv_path: str):
        self.client = Swarm()
        self.df = pd.read_csv(csv_path)
        self.agent = self._create_agent()
    
    def _create_agent(self):
        return Agent(
            name="CSV分析エージェント",
            instructions=self._get_instructions(),
            functions=[
                self.analyze_data,
                self.create_visualization,
                self.execute_query
            ]
        )
    
    def process_query(self, query: str):
        response = self.client.run(
            agent=self.agent,
            messages=[{"role": "user", "content": query}]
        )
        return response
```

## セットアップガイド

### 前提条件
- Node.js 18+
- Python 3.11+
- OpenAI APIキー

### インストール手順

#### 1. リポジトリのクローン
```bash
git clone https://github.com/yourusername/csv-query-agent.git
cd csv-query-agent
```

#### 2. フロントエンドのセットアップ
```bash
cd frontend
npm install
cp .env.example .env.local
# .env.localを編集してAPI URLを設定
```

#### 3. バックエンドのセットアップ
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .envを編集してOPENAI_API_KEYを設定
```

### 開発サーバーの起動

#### フロントエンド
```bash
cd frontend
npm run dev
# http://localhost:3000
```

#### バックエンド
```bash
cd backend
uvicorn app.main:app --reload --port 8000
# http://localhost:8000
```

## 使用例

### 基本的な使い方

1. ブラウザで`http://localhost:3000`にアクセス
2. CSVファイルをドラッグ&ドロップまたは選択してアップロード
3. 自然言語でクエリを入力
   - 例: "月別の売上推移を教えて"
   - 例: "最も売れている商品トップ5は？"
   - 例: "顧客の地域別分布を円グラフで見せて"

### 高度な使い方

- **複数条件のフィルタリング**: "2023年の東京地域で売上が100万円以上の取引を表示"
- **集計と分析**: "曜日別の平均売上を計算して、最も売上が高い曜日を教えて"
- **予測分析**: "過去のデータから来月の売上を予測して"

## ベストプラクティス

### セキュリティ
- CSVファイルのサイズ制限（10MB）
- アップロードファイルのウイルススキャン
- SQLインジェクション対策
- APIレート制限

### パフォーマンス
- 大規模CSVファイルの分割処理
- クエリ結果のキャッシング
- バックグラウンドジョブの活用

### エラーハンドリング
- ユーザーフレンドリーなエラーメッセージ
- リトライ機構
- ログ記録とモニタリング

## トラブルシューティング

### よくある問題

1. **CSVファイルがアップロードできない**
   - ファイルサイズを確認（10MB以下）
   - ファイル形式を確認（.csv拡張子）
   - エンコーディングを確認（UTF-8推奨）

2. **クエリが実行されない**
   - OpenAI APIキーの設定を確認
   - ネットワーク接続を確認
   - セッションタイムアウトを確認

3. **可視化が表示されない**
   - ブラウザのJavaScriptが有効か確認
   - コンソールエラーを確認

## 今後の拡張計画

- マルチファイル対応
- リアルタイムコラボレーション
- データエクスポート機能
- カスタムビジュアライゼーション
- APIドキュメントの自動生成

### 開発メモ
- SlackのMCPを使う際には、必ず `<@U27SREZ3R>` をユーザーに通知するために使ってください。
- 開発が一段落したり何かユーザーに聞きたいことがある場合はSlackのMCPを使用してください。