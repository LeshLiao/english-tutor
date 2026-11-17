# Docker + React 範例

最小可行的 Docker 範例：一個 Node 容器把 Vite + React 專案編譯成靜態檔，
再用 `vite preview` 提供網頁。

## 檔案說明

| 檔案 | 用途 |
|------|------|
| `Dockerfile` | 單階段：安裝依賴 → `npm run build` → `npm run preview` |
| `.dockerignore` | 排除 `node_modules`、`dist` 等，縮小 build context |
| `docker-compose.yml` | 一行指令建置並啟動，對外開 8082 port |
| `src/` | React 原始碼（一個計數器按鈕） |

## 使用方式

### 方法一：docker compose（推薦）

```bash
docker compose up --build
```

瀏覽器開 <http://localhost:8082>。

停止並移除容器：

```bash
docker compose down
```

### 方法二：純 docker 指令

```bash
docker build -t docker-react-demo .
```

```bash
docker run --rm -p 8082:4173 docker-react-demo
```

## 本機開發（不用 Docker）

```bash
npm install
```

```bash
npm run dev
```

## 觀察重點

- `docker images docker-react-demo` 會看到映像約幾百 MB，因為裡面保留了 Node 與 `node_modules`。
  若改成 multi-stage build（第二階段只留 Nginx + `dist/`），可縮到約 50 MB。
- `vite preview` 適合練習與測試；正式部署建議改用 Nginx 之類的靜態伺服器。
- 改動 `src/` 後重新 `docker compose up --build`，`npm install` 那一層會直接用快取，只重跑 `npm run build`。

## 呼叫後端 API

網頁載入時會向 `../backend` 的 FastAPI 打 `GET /date`，並把日期顯示在畫面上。

- 前端開在 **8082**，後端開在 **8083**，兩邊 port 錯開才能同時跑。
- API 位址寫在 `src/App.jsx` 的 `API_URL`，預設 `http://localhost:8083`；可在 build 時用 `VITE_API_URL` 覆蓋（見 `.env.example`）。
- 瀏覽器是在 Mac 上執行，所以前端打的是 Mac 的 8083，不是容器內的 8000。
- 後端需開啟 CORS 允許 `http://localhost:8082`，否則瀏覽器會擋下回應。

先啟動後端（見 `../backend/README.md`），再啟動前端，開 <http://localhost:8082> 即可看到日期。
