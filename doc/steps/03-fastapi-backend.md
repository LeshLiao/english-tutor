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

套件（`uv add`）：`fastapi`、`uvicorn[standard]`、`sqlalchemy`、`psycopg[binary]`、`alembic`、`pydantic-settings`。

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

在 `docker-compose.yml` 加入 `backend` 服務（掛載 `./backend:/app` 並加 `--reload` 做熱重載），完整內容見《本機架設規劃》。

### 3-6. Alembic migration

```powershell
docker compose up -d --build
docker compose exec backend alembic revision --autogenerate -m "init"
docker compose exec backend alembic upgrade head
```

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

### 3-8. 測試

用 `pytest` + `httpx` 至少寫：

- 沒帶 API key → 401。
- `POST /sentences` 帶新錯誤類型 → `error_types` 自動新增。
- `POST /sentences` 帶已存在類型 → 不重複新增。

## 完成條件

- [ ] http://localhost:8000/docs 正常
- [ ] Alembic migration 建出四張表（Adminer 可見）
- [ ] 無 API key 回 401
- [ ] `POST /sentences` 可寫入，新錯誤類型會自動建立
- [ ] pytest 全綠

## 下一步

→ [04-mcp-server.md](04-mcp-server.md)

## 實作紀錄

