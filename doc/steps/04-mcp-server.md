# 04. MCP Server（stdio）

## 目標

用 FastMCP 寫 MCP Server，先實作 `list_error_types` 與 `save_sentence` 兩個工具，以 stdio 模式註冊到 Claude Code，確認 `/mcp` 看得到工具。

MCP Server **不碰資料庫**，所有工具都呼叫 FastAPI。

## 前置條件

- [03](03-fastapi-backend.md) 完成，`GET /error-types` 與 `POST /sentences` 可用。

## 步驟

### 4-1. 建立 mcp-server 目錄

```
mcp-server/
├── Dockerfile        # 09 才會用到，可先留空
├── pyproject.toml
└── server.py
```

套件：`mcp`（官方 SDK，內含 FastMCP）、`httpx`。

```powershell
cd mcp-server
uv init
uv add mcp httpx
```

### 4-2. server.py 結構

- 用環境變數 `BACKEND_URL`（預設 `http://localhost:8000`）與 `API_KEY`。
- 用環境變數 `MCP_TRANSPORT`（`stdio` / `http`）決定啟動方式，預設 `stdio`。
- 建一個共用的 `httpx.Client`，每個請求帶 `X-API-Key` header。

### 4-3. 兩個工具

**`list_error_types()`**
- 呼叫 `GET /error-types`。
- 回傳現有類型清單（name + description），讓 Claude 分類時沿用，避免 "tense" 與 "verb tense" 重複。

**`save_sentence(original_text, corrected_text, explanation, source, errors)`**
- `errors` 為陣列，每項含 `error_type`、`error_snippet`、`suggestion`。
- 呼叫 `POST /sentences`。
- 回傳新建的 sentence id 與實際使用的錯誤類型（包含新建的）。

工具的 docstring 要寫清楚，Claude 是靠 docstring 決定怎麼用。

### 4-4. 本機執行測試

先確認 `docker compose up -d` 後端在跑，然後：

```powershell
cd mcp-server
uv run server.py
```

stdio 模式下不會有輸出，程式會等待 stdin，Ctrl+C 結束即可。
也可以用 MCP Inspector 測：

```powershell
npx @modelcontextprotocol/inspector uv run server.py
```

### 4-5. 註冊到 Claude Code

```powershell
claude mcp add english-practice -- uv --directory C:\Users\dlnx3\sourceCode\english-tutor\mcp-server run server.py
```

要把 `API_KEY` 傳進去可加 `-e API_KEY=dev-local-key`，或讓 server.py 自己讀專案根目錄 `.env`。

驗證：在 Claude Code 輸入 `/mcp`，應看到 `english-practice` 狀態為 connected，且列出兩個工具。

### 4-6. 用 Claude 直接呼叫測試

在 Claude Code 說：「請呼叫 list_error_types 看看有哪些類型」。
再說：「請用 save_sentence 存一句 'She don't like apple.'，修正為 'She doesn't like apples.'」。
到 Adminer 確認 `sentences` 多一筆。

## 完成條件

- [ ] `/mcp` 顯示 english-practice 已連線，列出 `list_error_types`、`save_sentence`
- [ ] Claude 呼叫 `list_error_types` 回傳與 Swagger 一致
- [ ] Claude 呼叫 `save_sentence` 後 Adminer 可見新資料
- [ ] 後端沒開時，工具回傳清楚的錯誤訊息而不是 crash

## 下一步

→ [05-claude-skill.md](05-claude-skill.md)

## 實作紀錄

