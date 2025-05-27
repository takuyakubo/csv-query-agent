FROM node:20-alpine

WORKDIR /app

# 依存関係をコピーしてインストール
COPY package*.json ./
RUN npm ci

# アプリケーションコードをコピー
COPY . .

# ポートを公開
EXPOSE 3000

# 開発サーバーを起動
CMD ["npm", "run", "dev"]