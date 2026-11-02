# 08. React 前端

## 目標

用 Vite + React + TypeScript 建三個頁面：總覽、句子列表、句子詳情，在瀏覽器查看統計與複習。

## 前置條件

- [07](07-remaining-tools-and-api.md) 完成，所有查詢 API 可用。

## 步驟

### 8-1. 建立專案

```bash
cd /Users/lesh/sourceCode/english-tutor
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

```bash
npm run dev
```

開 http://localhost:5173（終端機裡按 `o` 可直接開瀏覽器）：

- 總覽圖表數字與 Swagger `/stats/errors` 一致。
- 列表篩選 `tense` 後只剩該類句子。
- 詳情頁按「誤判」後，回總覽該類型數字減一。

> macOS 上第一次啟動 Vite 若跳出防火牆詢問，按允許。若 5173 被佔用，Vite 會自動往 5174 跳，此時 CORS 允許清單也要跟著加。

### 8-5. 容器版（選用，09 之前可先做）

`frontend/Dockerfile` 兩階段：`node:22-alpine` build → `nginx:alpine` 提供 `dist/`。
compose 裡 `frontend` 服務用 `profiles: ["prod"]`，開發時不啟動。

> `node:22-alpine` 與 `nginx:alpine` 都有 arm64 映像，Apple Silicon 可直接 build。[../aws/08-update-cicd.md](../aws/08-update-cicd.md) 的部署方式是在 Lightsail 主機（x86_64）上 `git pull` 後自行 build，所以不會遇到架構不符；只有改成「本機 build 推映像」時才需要加 `--platform linux/amd64`。

## 完成條件

- [x] 三個頁面都可用，資料與 API 一致（瀏覽器實測，總覽長條圖 6+5+2+2+1+1 = 17 與 `/stats/errors` 相同）
- [x] 篩選、分頁、誤判標記正常（篩 `tense` 剩 2 句；詳情頁標記 id 27 後總覽錯誤總數 17 → 15）
- [x] `npm run build` 無錯誤（`tsc -b && vite build`，oxlint 也乾淨）
- [x] （選用）`docker compose --profile prod up` 可在 http://localhost:**3001** 看到頁面（3000 被 open-webui 佔用）

## 下一步

→ [09-mcp-http-mode.md](09-mcp-http-mode.md)

## 實作紀錄

### 2026-11-02（Claude Code 協助）

**完成內容**
- `npx create-vite@latest frontend --template react-ts`（Vite 8、React 19、TypeScript 7、oxlint），再裝 `react-router-dom`、`@tanstack/react-query`、`recharts`。
- API 路徑統一走 `/api/*`：開發時 `vite.config.ts` 的 proxy 把 `/api` 轉到 `http://localhost:8000` 並去掉前綴；容器版由 nginx 做同一件事。`VITE_API_URL` 仍可覆寫成直連後端（此時才需要 CORS）。
- API key：`frontend/.env.development` 放 `VITE_API_KEY=dev-local-key`（與根目錄 `.env` 相同，是公開的開發預設值所以有進 git）。容器版 **不把 key 打進 bundle**：Dockerfile 把 `VITE_API_KEY` 清空，改由 nginx `proxy_set_header X-API-Key "${API_KEY}"` 注入，compose 的 `frontend` 服務從 `.env` 拿 `API_KEY`。驗證：`grep dev-local-key dist/assets/*.js` 無結果。
- backend：`config.py` 加 `cors_origins`（預設 5173、5174），`main.py` 掛 `CORSMiddleware`；pytest 補 preflight 測試，10 passed。
- 頁面：
  - `/` 總覽：四個數字方塊（錯誤類型數、錯誤總數、最近 30 天句子/錯誤）、各錯誤類型橫向長條圖、最近 30 天趨勢折線（後端只回有資料的日子，前端補 0）、最近 5 筆表格。
  - `/sentences` 列表：錯誤類型下拉（來自 `/error-types`）、日期從/到、關鍵字、顯示已誤判的核取方塊，條件都放在 URL query string 可分享；每頁 20 筆，回傳滿 20 筆才開放下一頁。
  - `/sentences/:id` 詳情：原句與修正句並排，自寫 LCS 字詞 diff（`src/diff.ts`）紅刪綠增；說明、錯誤清單（類型可點回列表篩選）；「標記為誤判 / 取消誤判標記」按鈕，成功後 invalidate 列表與統計的 query。
- 圖表顏色依 dataviz 指引：單一序列用 blue `#2a78d6`，趨勢兩條線 blue + orange，light/dark 兩組都跑過 `validate_palette.js` 全數 PASS；暗色模式用 `prefers-color-scheme`。
- `frontend/Dockerfile` 兩階段（node:22-alpine → nginx:alpine）、`nginx.conf.template`（SPA fallback + `/api/` 代理 + key 注入）、compose 加 `frontend` 服務（`profiles: ["prod"]`，port 3001）。`docker compose --profile prod build frontend` 在 Apple Silicon 直接成功。

**限制 / 待確認**
- bundle 748 kB（recharts 佔大半），Vite 提示可 code-split；個人使用先不處理。
- 趨勢圖的「日」是後端 `date_trunc` 的 UTC 日期，前端補 0 時用本地日期；台灣時間 08:00 前存的句子會算到前一天。等上雲或資料量大時再改成傳 timezone。
- 列表的「第 N 頁」沒有總筆數（API 沒回 total），只能用「滿 20 筆就有下一頁」判斷。
