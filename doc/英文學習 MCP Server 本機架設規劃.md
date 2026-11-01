# 英文學習 MCP Server 本機（Windows）架設規劃

## 目標

在上雲之前，先把整套系統（PostgreSQL、FastAPI、MCP Server、React）全部跑在本機 Windows 電腦上，用 Docker 管理各服務，驗證流程可行後再依《英文學習 MCP Server 規劃》搬到 AWS。

本機架構與雲端架構盡量一致：同一份 Docker 映像檔、同一套環境變數，日後搬家只需換掉部署方式與連線位址。

## 目前電腦狀態（2026-10-23 檢查）

| 工具 | 狀態 | 用途 |
|------|------|------|
| Windows 11 Home | 已有 | 作業系統 |
| Git 2.55 | 已安裝 | 版本控制 |
| Claude Code 2.1 | 已安裝 | Skill、Hook、MCP client |
| WSL2 | **未安裝** | Docker Desktop 必要元件 |
| Docker Desktop | **未安裝** | 執行容器 |
| Python | **未安裝** | FastAPI、MCP Server（本機開發用） |
| Node.js | **未安裝** | React 前端 |

## 第一步：安裝基礎工具

依序安裝，每一步完成後開新的終端機再繼續。

### 1. WSL2

以系統管理員身分開 PowerShell：

```powershell
wsl --install
```

安裝完需重新開機。重開後會自動跳出 Ubuntu 設定視窗，設好使用者名稱與密碼即可。

### 2. Docker Desktop

- 到 https://www.docker.com/products/docker-desktop/ 下載 Windows 版安裝。
- 安裝時勾選「Use WSL 2 instead of Hyper-V」。
- 安裝完後開啟 Docker Desktop，到 Settings → General 確認「Use the WSL 2 based engine」有勾選。
- Settings → Resources → WSL Integration，開啟 Ubuntu 的整合。
- 驗證：

```powershell
docker --version
docker compose version
docker run hello-world
```

### 3. Python 與 uv

Python 用於本機直接執行 MCP Server（stdio 模式）與開發除錯，容器內另有自己的 Python。

```powershell
winget install Python.Python.3.12
winget install astral-sh.uv
```

安裝後先到 Settings → Apps → Advanced app settings → App execution aliases，把 `python.exe` 與 `python3.exe` 的 Microsoft Store 捷徑關掉，否則會一直被導向商店。

驗證：

```powershell
python --version
uv --version
```

### 4. Node.js

```powershell
winget install OpenJS.NodeJS.LTS
```

驗證：

```powershell
node --version
npm --version
```

## 專案目錄結構

```
english-practice/
├── docker-compose.yml
├── .env                      # 本機環境變數（不進 git）
├── .env.example              # 環境變數範本
├── backend/                  # FastAPI
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic/
│   ├── alembic.ini
│   └── app/
│       ├── main.py
│       ├── models.py
│       ├── schemas.py
│       ├── db.py
│       └── routers/
│           ├── sentences.py
│           └── error_types.py
├── mcp-server/               # FastMCP
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── server.py
├── frontend/                 # React (Vite)
│   ├── Dockerfile
│   ├── package.json
│   └── src/
├── claude/                   # Claude Code 相關設定
│   ├── skills/
│   │   └── english-check/
│   │       └── SKILL.md
│   └── hooks/
│       └── check_english.py
└── doc/
```

## 本機服務架構

| 服務 | 執行方式 | 本機連接埠 | 說明 |
|------|----------|------------|------|
| PostgreSQL | Docker 容器 | 5432 | 資料掛載 Docker volume，重啟不丟資料 |
| FastAPI | Docker 容器 | 8000 | 唯一的資料讀寫入口；開發時掛載原始碼目錄，支援熱重載 |
| MCP Server | 第一階段：本機 Python（stdio）<br>第二階段：Docker 容器（Streamable HTTP） | 8001 | 透過 HTTP 呼叫 FastAPI，不直接連資料庫 |
| React | 第一階段：本機 `npm run dev`<br>第二階段：Docker 容器（nginx） | 5173 / 3000 | 開發時用 Vite dev server 比較方便 |
| Adminer（選用） | Docker 容器 | 8080 | 瀏覽器查看資料庫內容，方便除錯 |

**為什麼 MCP Server 第一階段用 stdio？**
Claude Code 在本機可以直接以子程序方式啟動 MCP Server，不需要網路、不需要認證，最快打通流程。等要上雲時再切換成 Streamable HTTP，程式碼只改啟動方式那一行。

## docker-compose.yml 規劃

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      timeout: 5s
      retries: 10

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      API_KEY: ${API_KEY}
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app          # 開發用熱重載
    depends_on:
      db:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  mcp:
    build: ./mcp-server
    environment:
      BACKEND_URL: http://backend:8000
      API_KEY: ${API_KEY}
      MCP_TRANSPORT: http
    ports:
      - "8001:8001"
    depends_on:
      - backend
    profiles: ["http"]        # 第二階段才啟用：docker compose --profile http up

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    profiles: ["prod"]        # 開發時用 npm run dev，不啟動這個

  adminer:
    image: adminer
    ports:
      - "8080:8080"
    depends_on:
      - db

volumes:
  pgdata:
```

## 環境變數（.env）

```
POSTGRES_USER=english
POSTGRES_PASSWORD=change-me
POSTGRES_DB=english_practice
API_KEY=dev-local-key
```

`.env` 加進 `.gitignore`，只提交 `.env.example`。

## 各服務細節

### PostgreSQL

- 使用官方 `postgres:16` 映像檔，不需自己寫 Dockerfile。
- 資料表由 FastAPI 的 Alembic migration 建立，不手動建。
- 備份：`docker compose exec db pg_dump -U english english_practice > backup.sql`。

### FastAPI

- 套件：`fastapi`、`uvicorn`、`sqlalchemy`、`psycopg[binary]`、`alembic`、`pydantic-settings`。
- 啟動時以 `X-API-Key` header 驗證，對應 `users.api_key`。
- 第一版 API：
  - `GET /error-types`
  - `POST /sentences`
  - `GET /sentences`（可依 error_type、日期篩選）
  - `GET /sentences/{id}`
  - `GET /stats/errors`
- Migration 指令在容器內執行：

```powershell
docker compose exec backend alembic revision --autogenerate -m "init"
docker compose exec backend alembic upgrade head
```

### MCP Server

- 套件：`mcp`（官方 SDK，內含 FastMCP）、`httpx`。
- 所有工具都是呼叫 FastAPI，自己不碰資料庫。
- 第一階段只實作 `list_error_types` 與 `save_sentence`。
- 用環境變數 `MCP_TRANSPORT` 決定 stdio 或 http，程式碼共用。
- 本機 stdio 啟動方式：

```powershell
cd mcp-server
uv sync
uv run server.py
```

### React

- 用 Vite 建立：`npm create vite@latest frontend -- --template react-ts`。
- 開發時 `npm run dev`，API 位址指向 `http://localhost:8000`。
- 容器版 Dockerfile 用兩階段：Node build 靜態檔，再用 nginx 提供。

## Claude Code 設定

### 註冊 MCP Server

第一階段（stdio，本機）：

```powershell
claude mcp add english-practice -- uv --directory C:\path\to\english-practice\mcp-server run server.py
```

第二階段（HTTP，容器）：

```powershell
claude mcp add --transport http english-practice http://localhost:8001/mcp --header "X-API-Key: dev-local-key"
```

驗證：在 Claude Code 裡輸入 `/mcp`，應看到 `english-practice` 與其工具清單。

### Skill

放在專案的 `.claude/skills/english-check/SKILL.md`，內容告訴 Claude：

1. 先呼叫 `list_error_types` 取得現有分類。
2. 檢查使用者給的句子，找出錯誤並沿用現有分類。
3. 呼叫 `save_sentence` 儲存結果。
4. 回覆修正句與說明。

### Hook（UserPromptSubmit）

`.claude/settings.json`：

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python C:\\path\\to\\english-practice\\claude\\hooks\\check_english.py"
          }
        ]
      }
    ]
  }
}
```

`check_english.py` 負責：

1. 從 stdin 讀取 prompt。
2. 過濾：只有包含英文句子、不含程式碼或中文、長度合理時才處理。
3. 用 `subprocess.Popen` 在背景啟動 `claude -p "<檢查指令>" --allowedTools mcp__english-practice__*`，立刻返回，不等待結果。
4. 輸出空字串，讓主對話不受影響。

## 啟動順序（日常開發）

```powershell
# 1. 啟動資料庫、後端、Adminer
docker compose up -d

# 2. 第一次或資料表有變更時
docker compose exec backend alembic upgrade head

# 3. 前端（另開終端機）
cd frontend
npm run dev

# 4. MCP Server 不用手動啟動，Claude Code 會自動以 stdio 啟動
```

停止：`docker compose down`。要連資料一起清掉：`docker compose down -v`。

## 驗證步驟

1. 開 http://localhost:8000/docs，確認 FastAPI Swagger 頁面正常。
2. 開 http://localhost:8080，用 .env 的帳密登入 Adminer，確認四張資料表存在。
3. 在 Claude Code 輸入 `/mcp`，確認 MCP Server 已連線且列出工具。
4. 手動請 Claude 檢查一句英文，確認 Adminer 裡 `sentences` 多了一筆。
5. 在 Claude Code 隨意輸入一句有錯的英文 prompt，等幾秒後確認 hook 有自動寫入。
6. 開 http://localhost:5173，確認總覽頁能顯示統計。

## 本機與雲端的差異

| 項目 | 本機 | AWS |
|------|------|-----|
| MCP 傳輸 | stdio（第一階段） | Streamable HTTP + 認證 |
| 資料庫 | Docker 容器 + volume | RDS |
| 密鑰 | `.env` 檔案 | Secrets Manager |
| HTTPS | 不需要 | ALB + 憑證 |
| 前端 | Vite dev server | S3 + CloudFront |
| 連線位址 | localhost | 網域名稱 |

程式碼不需要改，只需換環境變數與 compose/部署設定。

## Windows 特別注意事項

- **換行符號**：在專案根目錄放 `.gitattributes` 設定 `* text=auto eol=lf`，避免 shell script 進容器後因 CRLF 執行失敗。
- **Docker Desktop 資源**：預設會用掉不少記憶體，可在 `%UserProfile%\.wslconfig` 限制，例如 `memory=4GB`。
- **檔案掛載效能**：專案放在 Windows 磁碟（如 `C:\Users\...`）掛載到容器會比較慢，但個人專案可接受；若覺得慢可把專案移到 WSL 的檔案系統內。
- **防火牆**：第一次啟動 Docker Desktop 或 Vite 時 Windows 會跳出防火牆詢問，允許私人網路即可。
- **電腦睡眠**：若要讓 hook 在背景持續運作或遠端連線，把「睡眠」設為永不，螢幕關閉不影響。
- **路徑寫法**：`claude mcp add` 與 hook 設定裡的 Windows 路徑用 `\\` 或 `/` 都可以，但 JSON 內要用 `\\`。

## 實作順序建議

1. 安裝 WSL2、Docker Desktop、Python、uv、Node.js。
2. 建立專案目錄與 `docker-compose.yml`，先只跑 `db` 與 `adminer`，確認資料庫可連。
3. 寫 FastAPI 的 models、Alembic migration、`GET /error-types` 與 `POST /sentences`。
4. 寫 MCP Server 的 `list_error_types` 與 `save_sentence`，用 stdio 註冊到 Claude Code。
5. 寫 Skill，手動測試整個流程。
6. 寫 Hook，測試自動偵測。
7. 補其餘 MCP 工具與 API。
8. 建 React 前端三個頁面。
9. 把 MCP Server 改成 HTTP 模式跑在容器裡，為上雲做準備。
