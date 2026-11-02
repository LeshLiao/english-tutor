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
├── .python-version   # uv python pin 3.12 產生
└── server.py
```

套件：`mcp`（官方 SDK）、`httpx`。

```bash
cd mcp-server
uv init --bare --no-workspace --name english-mcp --python 3.12
uv python pin 3.12
uv add mcp httpx
```

> **mcp SDK 2.x 注意**：2026-11 裝到的是 mcp 2.3.0，`FastMCP` 已改名為 `MCPServer`（`from mcp.server.mcpserver import MCPServer`），`ToolError` 在 `mcp.server.mcpserver.exceptions`。網路上多數範例仍是 1.x 的 `from mcp.server.fastmcp import FastMCP`，照抄會 ImportError。

### 4-2. server.py 結構

- 用環境變數 `BACKEND_URL`（預設 `http://localhost:8000`）與 `API_KEY`。
- 用環境變數 `MCP_TRANSPORT`（`stdio` / `http`）決定啟動方式，預設 `stdio`。
- 建一個共用的 `httpx.Client`，每個請求帶 `X-API-Key` header。
- 後端連不到、timeout、401、其他非 2xx 都轉成 `ToolError`，訊息要寫明原因與處理方式。
- `API_KEY` 沒給時退回讀專案根目錄 `.env`（自己 parse，不裝 python-dotenv），這樣 `claude mcp add` 可以不用 `-e`。

### 4-3. 兩個工具

**`list_error_types()`**
- 呼叫 `GET /error-types`。
- 回傳現有類型清單（name + description），讓 Claude 分類時沿用，避免 "tense" 與 "verb tense" 重複。

**`save_sentence(original_text, corrected_text, explanation, source, errors)`**
- `errors` 為陣列，每項含 `error_type`、`error_snippet`、`suggestion`。
- 呼叫 `POST /sentences`。
- 回傳新建的 sentence id 與實際使用的錯誤類型（包含新建的）。

工具的 docstring 要寫清楚，Claude 是靠 docstring 決定怎麼用。`errors` 參數用 Pydantic model（`ErrorItem`）定義，每個欄位的 `Field(description=...)` 也會進 tool schema。

### 4-4. 本機執行測試

先確認 `docker compose up -d` 後端在跑，然後：

```bash
cd mcp-server
uv run server.py
```

stdio 模式下不會有輸出，程式會等待 stdin，Ctrl+C 結束即可。
也可以用 MCP Inspector 測：

```bash
npx @modelcontextprotocol/inspector uv run server.py
```

非互動的方式：用 SDK 的 `mcp.client.client.Client` 搭 `StdioServerParameters` 真的 spawn `uv run server.py` 子程序，列工具、呼叫工具、檢查 `is_error`（2.x 是 snake_case，不是 `isError`）。這和 Claude Code 的 stdio 連線方式完全相同。

### 4-5. 註冊到 Claude Code

```bash
claude mcp add english-practice -- /opt/homebrew/bin/uv --directory /Users/lesh/sourceCode/english-tutor/mcp-server run server.py
```

不加 `--scope` 就是 local scope，設定存在 `~/.claude.json`，只對這台 Mac 的這個專案有效。**不要用 `--scope project`**，那會產生含絕對路徑的 `.mcp.json` 進 git，Windows 機器用不了，而且每次還要審核。

要把 `API_KEY` 傳進去可加 `-e API_KEY=dev-local-key`，或讓 server.py 自己讀專案根目錄 `.env`。

> `uv` 在 `/opt/homebrew/bin`，Claude Code 從 GUI 啟動時 PATH 可能不含該路徑。若 `/mcp` 顯示 failed，改用絕對路徑 `/opt/homebrew/bin/uv`。

驗證：

```bash
claude mcp list    # 應顯示 english-practice ... ✔ Connected
```

再在 Claude Code 輸入 `/mcp`，應看到 `english-practice` 狀態為 connected，且列出兩個工具。已開著的 Claude Code session 不會自動載入新 MCP，要重開一次。

### 4-6. 用 Claude 直接呼叫測試

在 Claude Code 說：「請呼叫 list_error_types 看看有哪些類型」。
再說：「請用 save_sentence 存一句 'She don't like apple.'，修正為 'She doesn't like apples.'」。
到 Adminer 確認 `sentences` 多一筆。

## 完成條件

- [x] `claude mcp list` 顯示 ✔ Connected；SDK client 列出 `list_error_types`、`save_sentence`（`/mcp` 需重開 Claude Code 後確認）
- [x] `list_error_types` 回傳與 Swagger 一致
- [x] `save_sentence` 後資料庫可見新資料（id 17，source=skill，兩個錯誤）
- [x] 後端沒開時回傳 `Cannot reach backend at ... Is docker compose up -d running?`；API key 錯誤回傳 401 說明

## 下一步

→ [05-claude-skill.md](05-claude-skill.md)

## 實作紀錄

### 2026-11-02（Claude Code 協助）

**完成內容**
- `mcp-server/server.py`：mcp 2.3.0 的 `MCPServer`，兩個工具 `list_error_types`、`save_sentence`，共用 `httpx.Client`，錯誤統一轉 `ToolError`。`MCP_TRANSPORT=http` 分支先留著，步驟 09 再補。
- `Dockerfile` 先放註解佔位。
- 用 SDK `Client(StdioServerParameters(...))` 寫 smoke test（放 scratchpad，未進 repo）：列工具、兩個工具各呼叫一次、後端指到 8999 → `is_error=True` 訊息清楚、API_KEY 錯 → 401 訊息清楚。全部通過。
- `claude mcp add`（local scope）後 `claude mcp list` 顯示 ✔ Connected。

**踩到的坑**
- 一開始誤用 `--scope project`，產生 `.mcp.json` 且狀態為「Pending approval」，已移除改回 local scope。
- 2.x 的 `CallToolResult` 屬性是 `is_error` / `structured_content`，不是 1.x 的 `isError`。
- smoke test 跑兩次寫入兩筆相同句子，手動刪掉一筆。

**重開 Claude Code 後（同日）**：`english-practice` 工具已載入，Claude 直接呼叫 `list_error_types` 回傳三個類型，`save_sentence` 存入 id 19（`He is interesting in music.` → `word choice`），資料庫確認無誤。步驟 04 全部完成。

> 2026-11-02 起（[09](09-mcp-http-mode.md) 完成後）Claude Code 改以 HTTP 連 `http://localhost:8001/mcp`，本步驟的 stdio 註冊已移除；stdio 模式仍保留給本機除錯用。
