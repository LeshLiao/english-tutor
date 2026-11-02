# 02. 專案骨架與 PostgreSQL

## 目標

建立專案目錄結構與 `docker-compose.yml`，先只啟動 `db` 與 `adminer`，確認資料庫能跑、能連、重啟不丟資料。

## 前置條件

- [01](01-install-tools.md) 全部完成，Docker Desktop 在執行中。

## 步驟

### 2-1. 建立目錄結構

在專案根目錄（`/Users/lesh/sourceCode/english-tutor/`）建立：

```
english-tutor/
├── docker-compose.yml
├── .env                 # 不進 git
├── .env.example
├── .gitignore
├── .gitattributes
├── backend/             # 03 再填
├── mcp-server/          # 04 再填
├── frontend/            # 08 再填
├── claude/
│   └── hooks/           # skills 改放 lesh-marketplace 的 english-tutor-plugin，見 05
└── doc/
```

```bash
cd /Users/lesh/sourceCode/english-tutor
mkdir -p backend mcp-server frontend claude/hooks
```

### 2-2. 基本檔案

`.gitattributes`（macOS 本身是 LF，但這份 repo 也會在 Windows 機器上開發，統一強制 LF 避免 CRLF 進容器出錯）：

```
* text=auto eol=lf
```

`.gitignore` 至少包含：

```
.env
__pycache__/
.venv/
node_modules/
dist/
.DS_Store
```

> `.DS_Store` 是 macOS Finder 產生的隱藏檔，一定要排除。

`.env.example`：

```
POSTGRES_USER=english
POSTGRES_PASSWORD=change-me
POSTGRES_DB=english_practice
API_KEY=dev-local-key
```

複製一份成 `.env`，把密碼改掉：

```bash
cp .env.example .env
```

### 2-3. docker-compose.yml（第一版：只有 db 與 adminer）

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
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 10

  adminer:
    image: adminer
    ports:
      - "8081:8080"   # 本機 8080 被 Jenkins 佔用，對外改 8081
    depends_on:
      - db

volumes:
  pgdata:
```

`backend`、`mcp`、`frontend` 服務在後面步驟逐一加入（完整版見《本機架設規劃》）。

> Apple Silicon 上 `postgres:16` 與 `adminer` 都有原生 arm64 映像，不需要指定 `platform`。
>
> healthcheck 要加 `-d ${POSTGRES_DB}`，否則 `pg_isready` 會預設連同名資料庫 `english`，log 每 5 秒多一行 `FATAL: database "english" does not exist`（不影響運作，但很吵）。

### 2-4. 啟動與驗證

```bash
docker compose up -d
docker compose ps          # db 應為 healthy
docker compose logs db     # 看到 database system is ready to accept connections
```

開 http://localhost:8081，用 `.env` 的帳密登入 Adminer：

- System: PostgreSQL
- Server: `db`
- Username / Password / Database: 依 `.env`

> 若 5432 被佔用（例如之前用 Homebrew 裝過 `postgresql`），先 `brew services stop postgresql@16` 或把 compose 的對外 port 改成 `5433:5432`。

### 2-5. 驗證資料持久化

```bash
docker compose down
docker compose up -d
```

重啟後 Adminer 仍可登入，資料庫仍在（volume 沒被刪）。

> `docker compose down -v` 才會連資料一起刪，日常不要加 `-v`。

## 完成條件

- [x] `docker compose ps` 顯示 db 為 healthy
- [x] Adminer 可登入並看到空的 `english_practice` 資料庫（http://localhost:8081 回 200）
- [x] `down` → `up` 後資料庫仍在
- [x] `.env` 已在 `.gitignore`，`git status` 看不到它

## 下一步

→ [03-fastapi-backend.md](03-fastapi-backend.md)

## 實作紀錄

### 2026-11-02（Claude Code 協助）

- 建立目錄骨架、`.gitattributes`、`.gitignore`（含 `.DS_Store`）、`.env.example`、`.env`（密碼為隨機 24 字元）、第一版 `docker-compose.yml`。
- 本機 8080 被 Homebrew 安裝的 Jenkins（`jenkins-lts`）佔用，Adminer 對外 port 改為 **8081**，容器內仍是 8080。
- `docker compose up -d` 後 db 約 5 秒內 healthy；Adminer HTTP 200。
- healthcheck 原本沒帶 `-d`，log 持續出現 `FATAL: database "english" does not exist`，加上 `-d ${POSTGRES_DB}` 後消失。
- 持久化測試：建一張測試表寫入一筆 → `down` → `up` → 查詢仍為 1 筆 → 刪除測試表。volume `english-tutor_pgdata` 正常保留。
- 目前容器：`english-tutor-db-1`（postgres:16, healthy）、`english-tutor-adminer-1`。

