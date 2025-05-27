# CSV Query Agent

CSVファイルに対して自然言語でクエリを実行できるWebアプリケーション。OpenAI Swarm Agent SDKを使用してインテリジェントなデータ分析を実現します。

## 機能

- 📊 CSVファイルのドラッグ&ドロップアップロード
- 💬 自然言語でのデータクエリ
- 📈 自動グラフ生成（棒グラフ、折れ線グラフ、散布図など）
- 🔍 データ分析と統計情報の表示
- 🚀 リアルタイムレスポンス
- 🔐 セッション管理（30分間データ保持）

## 技術スタック

### Frontend
- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS
- Shadcn/ui
- React 19

### Backend
- Python 3.11+
- FastAPI
- OpenAI Swarm Agent SDK
- Pandas
- Redis (セッション管理)
- Matplotlib/Seaborn (可視化)

## セットアップ

### 前提条件
- Node.js 20+
- Python 3.11+
- Redis 7+
- OpenAI API Key

### インストール

1. リポジトリをクローン
```bash
git clone https://github.com/[your-username]/csv-query-agent.git
cd csv-query-agent
```

2. 環境変数の設定

Backend (.env):
```bash
cd backend
cp .env.example .env
# .envファイルを編集してOPENAI_API_KEYを設定
```

3. Redisの起動
```bash
# Dockerを使用
docker run -d --name csv-redis -p 6380:6379 redis:7-alpine

# または Homebrewを使用（macOS）
brew install redis
brew services start redis
```

4. Backendのセットアップ
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

5. Frontendのセットアップ
```bash
cd frontend
npm install
```

## 起動方法

### Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm run dev
```

アプリケーションは http://localhost:3000 でアクセスできます。

## 使い方

1. ブラウザで http://localhost:3000 にアクセス
2. CSVファイルをドラッグ&ドロップまたは選択してアップロード
3. 自然言語で質問を入力
   - 例：「売上金額の合計を教えて」
   - 例：「商品別の売上を棒グラフで表示」
   - 例：「店舗別の平均販売数量は？」
4. 結果とビジュアライゼーションが表示されます

## Docker Compose

```bash
docker-compose up -d
```

## API仕様

- `POST /upload` - CSVファイルのアップロード
- `POST /query` - 自然言語クエリの実行
- `GET /session/{session_id}` - セッション情報の取得
- `DELETE /session/{session_id}` - セッションの削除

詳細なAPI仕様は http://localhost:8000/docs で確認できます。

## プロジェクト構造

```
csv_query_agent/
├── frontend/          # Next.js フロントエンド
│   ├── app/          # App Router
│   ├── components/   # React コンポーネント
│   ├── lib/          # ユーティリティ
│   └── hooks/        # カスタムフック
├── backend/          # Python バックエンド
│   ├── app/          # FastAPI アプリケーション
│   ├── agents/       # OpenAI Swarm Agent 実装
│   └── services/     # ビジネスロジック
└── docker-compose.yml

```

## ライセンス

MIT

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを作成して変更内容について議論してください。

## 作者

[Your Name]