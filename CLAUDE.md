# CSV Query Agent - Project Context for Claude

## プロジェクト概要
CSVファイルに対して自然言語でクエリを実行できるWebアプリケーション。Next.js（App Router）とPython（OpenAI Agent SDK）を使用。

## 技術スタック
- **Frontend**: Next.js 14+ (App Router), TypeScript, Tailwind CSS, Shadcn/ui
- **Backend**: Python 3.11+, FastAPI, OpenAI Agent SDK, Pandas
- **AI**: OpenAI GPT-4o, OpenAI Agent SDK (旧Swarmから移行)

## ディレクトリ構造
```
csv_query_agent/
├── frontend/          # Next.jsフロントエンド
│   ├── app/          # App Router
│   ├── components/   # Reactコンポーネント
│   ├── lib/          # ユーティリティ
│   └── hooks/        # カスタムフック
├── backend/          # Pythonバックエンド
│   ├── app/          # FastAPIアプリケーション
│   ├── csv_agents/   # OpenAI Agent実装
│   ├── services/     # ビジネスロジック
│   └── gradio_app.py # Gradio UI
└── PROJECT_DOCUMENTATION.md  # 詳細ドキュメント
```

## 開発ガイドライン

### コーディング規約
- **TypeScript**: strictモード有効、型定義必須
- **Python**: PEP 8準拠、型ヒント使用
- **命名規則**: 
  - React: PascalCase（コンポーネント）、camelCase（関数）
  - Python: snake_case

### Git コミットメッセージ
- feat: 新機能
- fix: バグ修正
- docs: ドキュメント
- style: フォーマット
- refactor: リファクタリング
- test: テスト
- chore: その他

### 重要な実装ポイント

1. **CSVファイル処理**
   - 最大サイズ: 10MB
   - エンコーディング: UTF-8優先
   - Pandasでのメモリ効率的な処理

2. **OpenAI Agent実装**
   - OpenAI Agent SDKを使用 (旧Swarmから移行)
   - ツール: analyze_data, create_visualization, execute_query
   - セッション管理必須
   - output_type=ResponseCSVAgentで型安全なレスポンス

3. **API設計**
   - RESTful原則に従う
   - エラーレスポンスの統一フォーマット
   - CORSの適切な設定

4. **セキュリティ**
   - ファイルアップロードの検証
   - SQLインジェクション対策
   - API rate limiting実装

### テストコマンド
```bash
# Frontend
cd frontend
npm run lint
npm run type-check
npm run test

# Backend
cd backend
python -m pytest
python -m ruff check .
python -m mypy .
```

### 環境変数
```bash
# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Backend (.env)
OPENAI_API_KEY=your-api-key
REDIS_URL=redis://localhost:6379
MAX_FILE_SIZE=10485760  # 10MB
```

### よく使うコマンド
```bash
# 開発サーバー起動
cd frontend && npm run dev
cd backend && uvicorn app.main:app --reload

# ビルド
cd frontend && npm run build
cd backend && python -m build

# Docker
docker-compose up -d
```

### 注意事項
- OpenAI APIのレート制限に注意
- 大きなCSVファイルは分割処理を検討
- フロントエンドとバックエンドのポート衝突を避ける（3000, 8000）
- セッションは30分でタイムアウト

### 参考リンク
- [Next.js App Router Docs](https://nextjs.org/docs/app)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [OpenAI Agent SDK Docs](https://platform.openai.com/docs/assistants/overview)
- [Pandas Best Practices](https://pandas.pydata.org/docs/user_guide/best_practices.html)