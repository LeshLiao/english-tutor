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

- [ ] `docker compose --profile http up` 四個服務（db、backend、mcp、adminer）都 healthy
- [ ] Claude Code 以 HTTP 連上 MCP，工具可用
- [ ] 錯誤 API key 被拒絕
- [ ] Skill 與 Hook 回歸測試通過

## 下一步

→ [10-aws-deploy.md](10-aws-deploy.md)

## 實作紀錄

