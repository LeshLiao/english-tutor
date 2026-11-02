# 09. MCP Server 改 Streamable HTTP 並容器化

## 目標

讓 MCP Server 以 Streamable HTTP 模式跑在 Docker 容器裡，Claude Code 透過網址連線並帶 API key 認證。這是上雲前最後一步，之後只需改連線位址。

## 前置條件

- [08](08-react-frontend.md) 完成（或至少 [07](07-remaining-tools-and-api.md) 完成）。

## 步驟

### 9-1. server.py 支援 http

- `MCP_TRANSPORT=http` 時改用 `mcp.run(transport="streamable-http", host="0.0.0.0", port=8001)`。
- 加認證：檢查每個請求的 `X-API-Key` header（或 `Authorization: Bearer`），不符回 401。
- 工具要是無狀態的（不要在記憶體存 session 資料），之後才能水平擴展。

### 9-2. Dockerfile

`mcp-server/Dockerfile`：`python:3.12-slim` + uv，`CMD uv run server.py`，`EXPOSE 8001`。

### 9-3. compose 加入 mcp 服務

```yaml
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
    profiles: ["http"]
```

啟動：

```bash
docker compose --profile http up -d --build
```

### 9-4. 切換 Claude Code 連線方式

先移除 stdio 版：

```bash
claude mcp remove english-practice
claude mcp add --transport http english-practice http://localhost:8001/mcp --header "X-API-Key: dev-local-key"
```

`/mcp` 應顯示 connected，工具清單與之前相同。

> 改成 HTTP 後，[04](04-mcp-server.md) 提到的 Homebrew PATH 問題就不存在了，因為 Claude Code 不再需要自己啟動 `uv`。

### 9-5. 回歸測試

- `/english-check` 可用。
- Hook 自動儲存可用（`--allowedTools` 名稱不變）。
- 帶錯的 API key 連線 → 401：

```bash
curl -i -H "X-API-Key: wrong" http://localhost:8001/mcp
```

- 把 Docker 停掉再啟動，Claude Code 重連後正常。

### 9-6. 統一映像與環境變數

確認本機 compose 用的三個映像（backend、mcp、frontend）與《規劃》AWS 表格一致，環境變數只有 `.env` 一份，程式碼不含任何 localhost 硬編碼。

> Apple Silicon 本機 build 出來的映像是 arm64，不能直接拿到 x86_64 的雲端主機用。[../aws/08-update-cicd.md](../aws/08-update-cicd.md) 採「主機上自行 build」避開這個問題；若日後改成本機 build 推 ECR，要用 `docker buildx build --platform linux/amd64`。

## 完成條件

- [x] `docker compose --profile http up` 四個服務（db、backend、mcp、adminer）都 healthy
- [x] Claude Code 以 HTTP 連上 MCP，工具可用（`claude mcp list` → ✔ Connected，六個工具）
- [x] 錯誤 API key 被拒絕（錯誤 key 與沒帶 key 都 401；`/health` 免認證）
- [x] Skill 與 Hook 回歸測試通過（id 47 skill、id 48 hook；容器 stop/start 後自動重連）

## 下一步

→ [10-aws-deploy.md](10-aws-deploy.md)

## 實作紀錄

### 2026-11-02（Claude Code 協助）

**完成內容**
- `server.py`：`MCP_TRANSPORT=http` 時用 `mcp.streamable_http_app(streamable_http_path="/mcp", stateless_http=True, json_response=True)` 取得 Starlette app，再包一層自寫的純 ASGI `ApiKeyMiddleware`（`X-API-Key` 或 `Authorization: Bearer`，`hmac.compare_digest` 比對，不符 401），最後 `uvicorn.run`。`MCP_HOST`/`MCP_PORT` 預設 `0.0.0.0:8001`。`/health` 用 `@mcp.custom_route` 加在認證之外給 healthcheck 用。http 模式沒設 `API_KEY` 會拒絕啟動。工具本來就無狀態（每次都打後端），`stateless_http=True` 讓每個請求獨立、不在記憶體存 session。
- 認證用的 key 與打後端的 key 是同一把 `API_KEY`，`.env` 仍只有一份。`uvicorn` 加進 `pyproject.toml` 明確依賴。
- `mcp-server/Dockerfile`：與 backend 同樣的 `python:3.12-slim` + uv 寫法，venv 在 `/opt/venv`，`CMD python server.py`，`MCP_TRANSPORT=http` 在映像裡預設。`.dockerignore` 排除 `.venv`。
- compose 加 `mcp` 服務（`profiles: ["http"]`，port 8001，`BACKEND_URL=http://backend:8000`，healthcheck 打 `/health`）。
- Claude Code：`claude mcp remove english-practice` → `claude mcp add --transport http english-practice http://localhost:8001/mcp --header "X-API-Key: dev-local-key"`，local scope。

**實測**
- curl：`/health` 200 免 key；`X-API-Key: wrong` → 401；不帶 key 的 `tools/list` → 401；`Authorization: Bearer dev-local-key` 的 `tools/list` 回六個工具。
- MCP Python client（`streamable_http_client` + `httpx.AsyncClient(headers=...)`）列工具並呼叫 `get_error_stats`、`list_error_types` 成功。
- `claude -p "/english-tutor-plugin:english-check He don't like apple."` → 存成 id 47，附「最近第 N 次」標示。
- 以 stdin 模擬 hook 送 `We was late for the meeting yesterday.` → 約 20 秒後 id 48、`source = hook`。
- `docker compose stop mcp` 時 `claude mcp list` 顯示 ECONNREFUSED，`start` 後 6 秒內恢復 ✔ Connected。
- 9-6：程式碼裡的 `localhost` 只剩可被環境變數覆寫的預設值（backend `DATABASE_URL`/`CORS_ORIGINS`、mcp `BACKEND_URL`、Vite dev proxy）與容器內部的 healthcheck，沒有硬編碼。`--profile http --profile prod` 共五個服務：db、backend、mcp、frontend、adminer。

**限制 / 待確認**
- `stateless_http=True` 下 server 無法主動推送（notifications、sampling）；目前六個工具都不需要。
- 目前 `/mcp` 只在 localhost 用 HTTP 明文；上雲時由 Caddy 提供 HTTPS，key 不會明文走公網。
- 原本 stdio 版仍可用：`MCP_TRANSPORT` 不設即 stdio，`uv run server.py` 行為不變。
- 依 2026-11-02 的決定，MCP 改 HTTP 後可以把 hook 與 `.mcp.json` 搬進 `english-tutor-plugin`（連線網址 Mac/Windows 共用）；本步驟未做，留待使用者決定。
