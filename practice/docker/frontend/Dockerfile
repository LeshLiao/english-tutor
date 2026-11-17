# 單階段：一個 Node 映像包辦「編譯」與「提供網頁」
FROM node:22-alpine

WORKDIR /app

# 先複製 package.json 再安裝，讓 npm install 這層能被 Docker 快取
COPY package.json package-lock.json* ./
RUN npm install

# 複製其餘原始碼，把 React 編譯成 dist/ 靜態檔
COPY . .
RUN npm run build

# vite preview 預設監聽 4173，用來提供 dist/ 裡的靜態檔
EXPOSE 4173

CMD ["npm", "run", "preview"]
