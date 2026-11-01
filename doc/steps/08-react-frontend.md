# 08. React 前端

## 目標

用 Vite + React + TypeScript 建三個頁面：總覽、句子列表、句子詳情，在瀏覽器查看統計與複習。

## 前置條件

- [07](07-remaining-tools-and-api.md) 完成，所有查詢 API 可用。

## 步驟

### 8-1. 建立專案

```powershell
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install react-router-dom @tanstack/react-query recharts
```

### 8-2. API 設定

- `.env.development`：`VITE_API_URL=http://localhost:8000`、`VITE_API_KEY=dev-local-key`。
- 寫一個 `src/api.ts` 包 `fetch`，統一帶 `X-API-Key`。
- FastAPI 要加 CORS middleware，允許 `http://localhost:5173`。

> 第一版 API key 直接放前端只為本機方便；上雲前改成登入機制或至少改成反向代理注入。

### 8-3. 三個頁面

| 路由 | 頁面 | 資料來源 | 內容 |
|------|------|----------|------|
| `/` | 總覽 | `/stats/errors`、`/stats/trend` | 各錯誤類型次數長條圖；最近 30 天趨勢折線圖；最近 5 筆句子 |
| `/sentences` | 列表 | `/sentences` | 表格，可依錯誤類型、日期區間篩選、分頁；顯示 dismissed 的切換 |
| `/sentences/:id` | 詳情 | `/sentences/{id}` | 原句與修正句並排、diff 高亮、說明、錯誤清單；「標記為誤判」按鈕 |

### 8-4. 開發與驗證

```powershell
npm run dev
```

開 http://localhost:5173：

- 總覽圖表數字與 Swagger `/stats/errors` 一致。
- 列表篩選 `tense` 後只剩該類句子。
- 詳情頁按「誤判」後，回總覽該類型數字減一。

### 8-5. 容器版（選用，09 之前可先做）

`frontend/Dockerfile` 兩階段：`node:22-alpine` build → `nginx:alpine` 提供 `dist/`。
compose 裡 `frontend` 服務用 `profiles: ["prod"]`，開發時不啟動。

## 完成條件

- [ ] 三個頁面都可用，資料與 API 一致
- [ ] 篩選、分頁、誤判標記正常
- [ ] `npm run build` 無錯誤
- [ ] （選用）`docker compose --profile prod up` 可在 http://localhost:3000 看到頁面

## 下一步

→ [09-mcp-http-mode.md](09-mcp-http-mode.md)

## 實作紀錄

