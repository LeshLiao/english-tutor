# MCP server 練習

用最小的例子理解 MCP（Model Context Protocol）：一個 server 提供兩個工具，一個 client 連上去列出工具並呼叫。
正式版在專案根目錄的 `mcp-server/`，這裡只是練習場。

## 檔案

| 檔案 | 用途 |
|---|---|
| `test-server.py` | MCP server，名稱 `pos-server`，提供 `query_orders` 和 `query_today_date` 兩個工具，以 streamable-http 跑在 `http://127.0.0.1:8123/mcp` |
| `test-client.py` | 用 SDK 內建的 `Client` 模擬 AI 那一端：連線、列工具、呼叫一次 |
| `pyproject.toml` | 只宣告 `mcp>=2.3.0`，其餘 27 個套件是 mcp 的間接依賴 |
| `uv.lock` | 28 個套件的確切版本與雜湊，`uv sync` / `uv run` 照它裝出一樣的環境，要 commit |

## MCP 是什麼

把它想成「給 AI 用的 USB 介面」：

- **Server** 是你寫的程式，用 `@mcp.tool()` 註冊幾個 function。SDK 會把 function 的 type hint 翻成 `inputSchema`、docstring 變成 `description`，AI 靠這兩樣決定何時、怎麼呼叫。
- **Client** 是 AI 那一端（Claude Code、Claude Desktop、Cursor 等），連上 server 後問「你有哪些工具」，需要時呼叫。
- 兩邊講的語言是 **JSON-RPC 2.0**，傳輸方式有兩種，見下節。

## 環境與執行

這台 Mac 的 Homebrew Python 是 3.15，mcp 的依賴不保證有 3.15 的 wheel；3.12 只有 uv 管理的那份。所以一律用 uv。

```bash
cd practice/mcp-server
uv sync                      # 第一次或 pull 後：照 uv.lock 建 .venv
```

開兩個終端機：

```bash
# 終端機 1：server 常駐
uv run test-server.py        # 看到 Uvicorn running on http://127.0.0.1:8123 即可

# 終端機 2：client 連過去
uv run test-client.py
```

預期輸出：

```
tool: query_orders | 查詢某一天的訂單數量和營業額。date 格式為 YYYY-MM-DD。
tool: query_today_date | 查詢今天幾月幾號
result: [TextContent(type='text', text='{"date": "2026-11-08", "total": 128, "revenue": 35600}')]
```

### 兩種 transport

| | stdio | streamable-http |
|---|---|---|
| 怎麼連 | client 把 server 當子程序啟動，用 stdin/stdout 傳 JSON-RPC | server 常駐聽一個 port，client 用 URL 連 |
| server 端 | `mcp.run()` | `mcp.run(transport="streamable-http", host="127.0.0.1", port=8123)` |
| client 端 | `Client(StdioServerParameters(command="python", args=["test-server.py"]))` | `Client("http://127.0.0.1:8123/mcp")` |
| session | 一個子程序就是一個 session | 回應 header 帶 `mcp-session-id`，後續請求要帶回 |
| 適合 | 本機工具，Claude Code / Desktop 預設 | 遠端或容器，正式版 `mcp-server/` 就是這種 |

單獨跑 stdio 模式的 server 畫面會停住，那是在等 stdin，不是壞掉。

## JSON-RPC 流程圖

標 ★ 的是只註冊 tools 的最小 server 實際會用到的方法。

```
   Client（Claude Code / test-client.py）              Server（test-server.py）
   ─────────────────────────────────────              ───────────────────────
 ┌─ 1. 生命週期（每次連線必經）──────────────────────────────────────────┐
 │  ★ initialize ──────────────────────────────────▶                     │
 │      協定版本、client 能力、client 名字                                │
 │  ◀────────────────────────── result: 協定版本、server 能力、server 名字 │
 │  ★ notifications/initialized ───────────────────▶  （通知，不回覆）    │
 │      「我準備好了」，之後才能發功能請求                                │
 │  ping ◀─────────────────────────────────────────▶  （雙向，可隨時發）  │
 └────────────────────────────────────────────────────────────────────────┘

 ┌─ 2. 探索：server 有什麼？────────────────────────────────────────────┐
 │  ★ tools/list ──────────────────────────────────▶                     │
 │  ◀──────────── 工具清單：name、description、inputSchema                │
 │    resources/list / resources/templates/list ───▶   唯讀資料          │
 │    prompts/list ────────────────────────────────▶   提示範本          │
 └────────────────────────────────────────────────────────────────────────┘

 ┌─ 3. 使用：AI 決定要做什麼時 ──────────────────────────────────────────┐
 │  ★ tools/call {name, arguments} ────────────────▶                     │
 │  ◀──────────────────── result: content[] / structuredContent          │
 │    resources/read {uri} ────────────────────────▶                     │
 │    resources/subscribe / unsubscribe ───────────▶                     │
 │    prompts/get {name, arguments} ───────────────▶                     │
 │    completion/complete ─────────────────────────▶   參數自動補全      │
 │    logging/setLevel ────────────────────────────▶                     │
 └────────────────────────────────────────────────────────────────────────┘

 ┌─ 4. 反向請求：server → client ────────────────────────────────────────┐
 │  ◀──────────────────────────────── sampling/createMessage              │
 │      server 請 client 的 LLM 生成一段文字                              │
 │  ◀──────────────────────────────── elicitation/create                  │
 │      server 請 client 向使用者問一個問題                               │
 │  ◀──────────────────────────────── roots/list                          │
 │      server 問 client 可以存取哪些目錄                                 │
 └────────────────────────────────────────────────────────────────────────┘

 ┌─ 5. 通知（單向、不需回覆）────────────────────────────────────────────┐
 │  ◀──── notifications/tools/list_changed        工具清單變了，請重抓    │
 │  ◀──── notifications/resources/list_changed                            │
 │  ◀──── notifications/resources/updated         訂閱的資源變了          │
 │  ◀──── notifications/prompts/list_changed                              │
 │  ◀──── notifications/message                   server 的 log           │
 │  ◀───▶ notifications/progress                  長任務進度（雙向）      │
 │  ◀───▶ notifications/cancelled                 取消某個請求（雙向）    │
 │  ────▶ notifications/roots/list_changed                                │
 └────────────────────────────────────────────────────────────────────────┘

   連線結束：沒有 shutdown 訊息，直接關 transport
   （stdio 關 stdin；HTTP 送 DELETE /mcp 帶 session id）
```

### 標準方法分級（規格 2025-06-18）

- **強制**：`initialize`、`notifications/initialized`。沒做完這兩步，server 應拒絕其他請求。
- **Server 能力，各自選用**：tools、resources、prompts。server 在 initialize 回應中宣告支援哪些。九成以上的 server 只做 tools。
- **Client 能力，選用**：sampling、elicitation、roots。由 client 在 initialize 時宣告。
- **工具類**：ping、progress、cancelled、logging、completion。標準但簡單實作常不用。

### SDK 幫你做掉的部分

| 標準方法 | test-client.py 裡的對應 |
|---|---|
| initialize + initialized | `async with Client(...)` 進入時自動做 |
| tools/list | `client.list_tools()` |
| tools/call | `client.call_tool(name, args)` |
| DELETE session | 離開 `async with` 時自動做 |

## 用 curl 手動走一次 HTTP session

不靠 SDK，親眼看每一步。HTTP 層的規則很單純：**所有 JSON-RPC 訊息都 POST 到同一個 `/mcp`**，方法名寫在 body 的 `method`。只有結束 session 用 DELETE。GET `/mcp` 是給 server 主動推訊息用的長連線，這個範例用不到。

每個請求都要帶 `Content-Type: application/json` 和 `Accept: application/json, text/event-stream`，少了 Accept 會被拒絕。

**1. initialize，拿 session id**

```bash
curl -s http://127.0.0.1:8123/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl","version":"0"}}}' -i
```

回應 header 有 `mcp-session-id`，body 是 SSE 格式（`event: message` + `data: {...}`），裡面是 server 名字、協定版本、支援的能力。把 id 存起來：

```bash
SID=<回應裡的 mcp-session-id>
```

**2. notifications/initialized**（沒有 id，是通知，server 回 202 沒內容）

```bash
curl -s http://127.0.0.1:8123/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "Mcp-Session-Id: $SID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}' -i
```

**3. tools/list**

```bash
curl -s http://127.0.0.1:8123/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "Mcp-Session-Id: $SID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
```

**4. tools/call**

```bash
curl -s http://127.0.0.1:8123/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "Mcp-Session-Id: $SID" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"query_orders","arguments":{"date":"2026-11-08"}}}'
```

**5. 結束 session**

```bash
curl -s -X DELETE http://127.0.0.1:8123/mcp -H "Mcp-Session-Id: $SID" -i
```

server 重啟後 session id 失效，會收到 404 或 session not found，重做第 1 步即可。
回應是 SSE 而不是純 JSON，是因為 POST 的回應可以串流，server 能先推進度再回結果。server 端設 `json_response=True` 就會改回 `application/json`，正式版 `mcp-server/server.py` 就是這樣。

## mcp 2.x 與網路教學的差異

網路上大多數教學還是 mcp 1.x，看到時把這幾個換掉即可：

| 1.x | 2.x |
|---|---|
| `from mcp.server.fastmcp import FastMCP` | `from mcp.server.mcpserver import MCPServer` |
| `tool.inputSchema` | `tool.input_schema` |
| `result.structuredContent` | `result.structured_content` |

遷移說明：https://py.sdk.modelcontextprotocol.io/v2/migration/

## 下一步

- 把 `query_orders` 換成真的查資料（讀 JSON 檔或 SQLite），看 AI 怎麼用它。
- 掛進 Claude Code 真的給 AI 用：`claude mcp add --transport http pos-server http://127.0.0.1:8123/mcp`，開新 session 問「11 月 8 日營業額多少」。
- 回頭讀正式版 `mcp-server/server.py` 的 `build_http_app`：它多了 API key middleware、`stateless_http=True`，以及用環境變數切換 stdio / http。
