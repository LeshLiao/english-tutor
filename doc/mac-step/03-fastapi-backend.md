# 03. FastAPI 後端

## 目標

建立 FastAPI 後端，用 SQLAlchemy 定義四張資料表、Alembic 建表，並提供第一版 API。
後端是**所有資料讀寫的唯一入口**，MCP Server 與前端都只透過它存取資料。

## 前置條件

- [02](02-docker-postgres.md) 完成，資料庫可連。

## 步驟

### 3-1. 建立 backend 目錄

```
backend/
├── Dockerfile
├── pyproject.toml
├── .python-version     # uv python pin 3.12 產生
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
└── app/
    ├── __init__.py
    ├── main.py
    ├── config.py       # pydantic-settings 讀環境變數
    ├── db.py           # engine、session
    ├── models.py       # SQLAlchemy models
    ├── schemas.py      # Pydantic schemas
    ├── auth.py         # X-API-Key 驗證
    └── routers/
        ├── error_types.py
        ├── sentences.py
        └── stats.py
```

初始化並安裝套件：

```bash
cd backend
uv init --bare --no-workspace --name english-backend --python 3.12
uv python pin 3.12
uv add fastapi "uvicorn[standard]" sqlalchemy "psycopg[binary]" alembic pydantic-settings
uv add --dev pytest httpx
```

> zsh 會把 `[]` 當 glob，所以 `uvicorn[standard]`、`psycopg[binary]` 必須加引號。

### 3-2. 資料表（models.py）

| 表 | 欄位 |
|----|------|
| `users` | id, name, api_key (unique), created_at |
| `sentences` | id, user_id (FK), original_text, corrected_text, explanation, source (`hook` / `skill`), is_dismissed (bool, default false), created_at |
| `error_types` | id, name (unique), description, created_at |
| `sentence_errors` | id, sentence_id (FK), error_type_id (FK), error_snippet, suggestion |

> `is_dismissed` 是規劃文件「待釐清」提到的誤判回饋欄位，一開始就加，避免之後再 migration。

### 3-3. 認證（auth.py）

- 讀 request header `X-API-Key`，查 `users.api_key`，找不到回 401。
- 回傳 `User` 物件，讓每個 router 用 `user.id` 過濾資料。
- 第一次啟動時用 seed script 或 migration 建一個預設使用者，`api_key` 取自 `.env` 的 `API_KEY`。

### 3-4. 第一版 API

| Method | Path | 說明 |
|--------|------|------|
| GET | `/error-types` | 列出所有錯誤類型 |
| POST | `/sentences` | 儲存一筆句子與其錯誤；body 內錯誤類型用 `name` 指定，不存在則自動新增 |
| GET | `/sentences` | 列表，支援 `error_type`、`from`、`to` 查詢參數 |
| GET | `/sentences/{id}` | 單筆詳情（含錯誤明細） |
| GET | `/stats/errors` | 各錯誤類型次數，支援時間範圍 |
| GET | `/health` | 健康檢查（給 Docker / 之後 K8s 用） |

本步驟**至少完成** `/error-types`、`POST /sentences`、`/health`，其餘可在 [07](07-remaining-tools-and-api.md) 補。

### 3-5. Dockerfile 與 compose

`backend/Dockerfile`：以 `python:3.12-slim` 為底，用 uv 安裝依賴，`CMD uvicorn app.main:app --host 0.0.0.0 --port 8000`。

> **重點**：Dockerfile 設 `UV_PROJECT_ENVIRONMENT=/opt/venv`，讓 venv 放在 `/app` 之外。否則 `./backend:/app` bind mount 會把 macOS 的 `.venv`（arm64 Mach-O 二進位）蓋進 Linux 容器，uvicorn 會起不來。

在 `docker-compose.yml` 加入 `backend` 服務（掛載 `./backend:/app` 並加 `--reload` 做熱重載），完整內容見《本機架設規劃》。

compose 的 `command` 用 `sh -c "alembic upgrade head && uvicorn ... --reload"`，每次容器啟動都先套用 migration，之後 `docker compose restart backend` 就會自動建表。

> macOS 上 bind mount 走 VirtioFS，`--reload` 的檔案變更偵測偶爾會慢一兩秒，屬正常。若完全不觸發，在 Docker Desktop → Settings → General 確認檔案共享實作是 VirtioFS。

### 3-6. Alembic migration

```bash
docker compose up -d --build
docker compose exec backend alembic revision --autogenerate -m "init"
docker compose exec backend alembic upgrade head
docker compose restart backend     # 讓 startup 的 seed 建出預設使用者
```

第一次 `up` 時 backend log 會出現 `seed skipped ... relation "users" does not exist`，這是正常的，migration 跑完再 restart 就會看到 `seeded default user`。

> 容器內以 root 執行時，autogenerate 產生的 `alembic/versions/*.py` 在 macOS 端會是 root 擁有；Docker Desktop 會自動對應成本機使用者，通常不用處理。若 `git add` 時遇到權限問題，`sudo chown -R $(whoami) backend/alembic/versions`。

### 3-7. 手動測試

- 開 http://localhost:8000/docs（Swagger）。
- 在 Swagger 右上 Authorize 填 `X-API-Key`。
- `GET /error-types` → 空陣列。
- `POST /sentences` 送一筆範例：

```json
{
  "original_text": "I go to school yesterday.",
  "corrected_text": "I went to school yesterday.",
  "explanation": "Past time marker requires past tense.",
  "source": "skill",
  "errors": [
    { "error_type": "tense", "error_snippet": "go", "suggestion": "went" }
  ]
}
```

- 再 `GET /error-types` → 應出現 `tense`。
- Adminer 裡 `sentences` 與 `sentence_errors` 各多一筆。

也可以直接用 curl：

```bash
curl -s -H "X-API-Key: dev-local-key" http://localhost:8000/error-types
```

### 3-8. 測試

用 `pytest` + `httpx` 至少寫：

- 沒帶 API key → 401。
- `POST /sentences` 帶新錯誤類型 → `error_types` 自動新增。
- `POST /sentences` 帶已存在類型 → 不重複新增。

測試跑在真實的 PostgreSQL 上，每個測試包在一個外層交易內、結束後 rollback，不會留下資料。`error_types` 是全域表，測試要用隨機類型名稱，不能寫死 `tense`。

在容器內或本機執行皆可：

```bash
docker compose exec backend pytest
# 或本機（要指到容器的 5432，密碼取自 .env）
cd backend
DATABASE_URL="postgresql+psycopg://english:<密碼>@localhost:5432/english_practice" uv run pytest
```

## 完成條件

- [x] http://localhost:8000/docs 正常
- [x] Alembic migration 建出四張表（Adminer 可見）
- [x] 無 API key 回 401
- [x] `POST /sentences` 可寫入，新錯誤類型會自動建立
- [x] pytest 全綠（容器內與本機各跑一次）

## 下一步

→ [04-mcp-server.md](04-mcp-server.md)

## 實作紀錄

### 2026-11-02（Claude Code 協助）

**完成內容**
- `uv init --bare` + `uv python pin 3.12`；套件版本：FastAPI 0.162、SQLAlchemy 2.1.6、psycopg 3.3.6、Alembic 1.20、pydantic-settings 2.16；dev：pytest 9.2、httpx 0.28。
- 六個 endpoint 全部做完（`/health`、`GET /error-types`、`POST /sentences`、`GET /sentences`（支援 `error_type`、`from`、`to`、`limit`、`offset`、`include_dismissed`）、`GET /sentences/{id}`、`GET /stats/errors`），不只最低要求的三個。
- 錯誤類型名稱存入前會 `strip().lower()`，所以 `Tense ` 與 `tense` 視為同一類。
- 預設使用者在 app startup 的 lifespan 裡 seed（找不到就建、api_key 不同就更新），不是放在 migration。
- migration `ab2b8cca986e_init.py` 由容器內 autogenerate，檔案在 Mac 端 owner 正確是 lesh，不需 chown。
- 手動 curl：無 key 401、POST 回 201、`error_types` 自動出現 `tense`、`/stats/errors` 計數 1。
- pytest 6 個案例全綠，連跑兩次資料庫列數不變；熱重載測試 `touch app/schemas.py` 後 WatchFiles 約 1 秒內重啟。

**踩到的坑**
- 第一版測試寫死 `tense`，被手動 curl 建的資料干擾而失敗 → 改成每個測試用 uuid 當類型名。
- `starlette.testclient` 對 httpx 印 deprecation warning（建議改裝 `httpx2`），目前不影響，先不處理。

**目前狀態**：`docker compose ps` 三個服務（db、backend、adminer）皆 healthy / Up。

