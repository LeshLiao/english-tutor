# 02. 專案骨架與 PostgreSQL

## 目標

建立專案目錄結構與 `docker-compose.yml`，先只啟動 `db` 與 `adminer`，確認資料庫能跑、能連、重啟不丟資料。

## 前置條件

- [01](01-install-tools.md) 全部完成。

## 步驟

### 2-1. 建立目錄結構

在專案根目錄（`english-tutor/`）建立：

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
│   ├── skills/
│   └── hooks/
└── doc/
```

### 2-2. 基本檔案

`.gitattributes`（避免 CRLF 進容器出錯）：

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
```

`.env.example`：

```
POSTGRES_USER=english
POSTGRES_PASSWORD=change-me
POSTGRES_DB=english_practice
API_KEY=dev-local-key
```

複製一份成 `.env`，把密碼改掉。

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
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      timeout: 5s
      retries: 10

  adminer:
    image: adminer
    ports:
      - "8080:8080"
    depends_on:
      - db

volumes:
  pgdata:
```

`backend`、`mcp`、`frontend` 服務在後面步驟逐一加入（完整版見《本機架設規劃》）。

### 2-4. 啟動與驗證

```powershell
docker compose up -d
docker compose ps          # db 應為 healthy
docker compose logs db     # 看到 database system is ready to accept connections
```

開 http://localhost:8080，用 `.env` 的帳密登入 Adminer：

- System: PostgreSQL
- Server: `db`
- Username / Password / Database: 依 `.env`

### 2-5. 驗證資料持久化

```powershell
docker compose down
docker compose up -d
```

重啟後 Adminer 仍可登入，資料庫仍在（volume 沒被刪）。

> `docker compose down -v` 才會連資料一起刪，日常不要加 `-v`。

## 完成條件

- [ ] `docker compose ps` 顯示 db 為 healthy
- [ ] Adminer 可登入並看到空的 `english_practice` 資料庫
- [ ] `down` → `up` 後資料庫仍在
- [ ] `.env` 已在 `.gitignore`，`git status` 看不到它

## 下一步

→ [03-fastapi-backend.md](03-fastapi-backend.md)

## 實作紀錄

