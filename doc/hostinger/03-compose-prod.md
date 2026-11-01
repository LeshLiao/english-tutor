# 03. 正式版 docker-compose 與啟動

## 目標

寫一份獨立的 `docker-compose.prod.yml`：不掛原始碼、不開 `--reload`、不對外開 port、
加 `restart`，並加入 Caddy 服務。在 VPS 上 build 並啟動，確認五個容器都 healthy。

## 前置條件

- [02](02-server-setup.md) 完成。
- 本機 `docker compose --profile http --profile prod up` 已能正常運作（steps/09）。

## 步驟

### 3-1. 在 repo 根目錄新增 `docker-compose.prod.yml`

用獨立檔案而不是 override，避免 profile 與 `ports` 覆蓋問題，Hostinger Docker Manager 也能直接讀。

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      timeout: 5s
      retries: 10
    restart: unless-stopped

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      API_KEY: ${API_KEY}
      CORS_ORIGINS: https://${DOMAIN}
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  mcp:
    build: ./mcp-server
    environment:
      BACKEND_URL: http://backend:8000
      API_KEY: ${API_KEY}
      MCP_TRANSPORT: http
    depends_on:
      - backend
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_URL: https://${DOMAIN}/api
    depends_on:
      - backend
    restart: unless-stopped

  caddy:
    image: caddy:2
    ports:
      - "80:80"
      - "443:443"
    environment:
      DOMAIN: ${DOMAIN}
      API_KEY: ${API_KEY}
    volumes:
      - ./deploy/Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - backend
      - mcp
      - frontend
    restart: unless-stopped

volumes:
  pgdata:
  caddy_data:
  caddy_config:
```

重點差異（對照本機版）：

| 項目 | 本機 | 正式 |
|------|------|------|
| `ports:` | db/backend/mcp/frontend 都開 | **只有 caddy** 開 80/443 |
| backend `volumes: ./backend:/app` | 有（熱重載） | 無，程式碼 build 進映像 |
| uvicorn `--reload` | 有 | 無 |
| adminer | 有 | 無（要看資料庫用 06 的 `psql` 或 SSH tunnel） |
| `restart` | 無 | `unless-stopped`，重開機自動起來 |
| profiles | http / prod | 不用，全部都是正式服務 |

### 3-2. 程式端要配合的小修改

- **backend**：CORS 來源改讀環境變數 `CORS_ORIGINS`（逗號分隔），本機預設 `http://localhost:5173`。
- **frontend Dockerfile**：build 階段加 `ARG VITE_API_URL` 與 `ENV VITE_API_URL=$VITE_API_URL`，再 `npm run build`。
- **frontend**：移除 `VITE_API_KEY`，前端不再帶 key，改由 Caddy 注入（見 04）。
- **backend 啟動時跑 migration**：在 Dockerfile 的 entrypoint 或 compose `command` 前加 `uv run alembic upgrade head &&`，
  或每次部署手動跑（見 3-4）。

先在本機用 `docker compose -f docker-compose.prod.yml config` 檢查語法再 commit。

### 3-3. 暫時版 Caddyfile（先用 IP 測試，04 再換網域）

建立 `deploy/Caddyfile`：

```
:80 {
    handle /api/* {
        uri strip_prefix /api
        reverse_proxy backend:8000
    }
    handle /mcp* {
        reverse_proxy mcp:8001
    }
    handle {
        reverse_proxy frontend:80
    }
}
```

### 3-4. 在 VPS 上 build 與啟動

```bash
cd /srv/english-tutor
git pull
docker compose -f docker-compose.prod.yml build      # 第一次約 3–5 分鐘
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml ps          # 五個都 Up / healthy
docker compose -f docker-compose.prod.yml exec backend uv run alembic upgrade head
```

> KVM 1 只有 1 vCPU，frontend 的 `npm run build` 會比本機慢，屬正常。若記憶體不足被 kill，先確認 02 的 swap 有開。

### 3-5. 驗證

```bash
curl -s http://localhost/api/docs | head -5                       # FastAPI Swagger HTML
curl -s -o /dev/null -w "%{http_code}\n" http://localhost/mcp     # 401（沒帶 key）
curl -s http://localhost/ | grep -o "<title>.*</title>"           # 前端 index.html
docker compose -f docker-compose.prod.yml logs --tail 50 backend
```

從本機瀏覽器開 `http://<VPS_IP>/` 應看到前端（API 還不通，04 設好網域後才會）。

確認沒有多開 port：

```bash
ss -tlnp | grep -E ':(5432|8000|8001|3000|8080)\b' || echo "OK: nothing exposed"
```

## 完成條件

- [ ] `docker compose -f docker-compose.prod.yml ps` 五個服務 Up，db healthy
- [ ] `ss -tlnp` 只看到 22、80、443
- [ ] `http://<VPS_IP>/api/docs` 可開
- [ ] `/mcp` 沒帶 key 回 401
- [ ] `docker-compose.prod.yml` 與 `deploy/Caddyfile` 已 commit

## 下一步

→ [04-domain-caddy-https.md](04-domain-caddy-https.md)

## 實作紀錄

（填寫日期、遇到的問題與解法）
