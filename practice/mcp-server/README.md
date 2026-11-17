# MCP server 練習

用最小的例子理解 MCP（Model Context Protocol）：一個 server 提供 tools、resources、prompts 三種能力各一兩個，一個 client 連上去列出、呼叫、讀取。
正式版在專案根目錄的 `mcp-server/`，這裡只是練習場。

## 檔案

| 檔案             | 用途                                                                                                                                   |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `test-server.py` | MCP server，名稱 `pos-server`：兩個 tool（`query_orders`、`query_today_date`）、一個 resource（`pos://store/info`）、一個 resource template（`pos://orders/{date}`）、一個 prompt（`daily_report`），以 streamable-http 跑在 `http://127.0.0.1:8123/mcp` |
| `test-client.py` | 用 SDK 內建的 `Client` 模擬 AI 那一端：連線後把 tools / resources / prompts 三種清單都列出來，各用一次                                      |
| `pyproject.toml` | 只宣告 `mcp>=2.3.0`，其餘 27 個套件是 mcp 的間接依賴                                                                                   |
| `uv.lock`        | 28 個套件的確切版本與雜湊，`uv sync` / `uv run` 照它裝出一樣的環境，要 commit                                                          |

## MCP 是什麼

把它想成「給 AI 用的 USB 介面」：

- **Server** 是你寫的程式，用 `@mcp.tool()`、`@mcp.resource()`、`@mcp.prompt()` 註冊幾個 function。SDK 會把 function 的 type hint 翻成 schema、docstring 或 `description=` 變成說明，AI 靠這些決定何時、怎麼用。
- **Client** 是 AI 那一端（Claude Code、Claude Desktop、Cursor 等），連上 server 後問「你有哪些 tools / resources / prompts」，需要時呼叫或讀取。
- 兩邊講的語言是 **JSON-RPC 2.0**，傳輸方式有兩種，見下節。

### 三種能力的差別

| 能力      | 誰決定要用  | server 端寫法                                    | 探索方法                                   | 使用方法                   | 例子                                      |
| --------- | ----------- | ------------------------------------------------ | ------------------------------------------ | -------------------------- | ----------------------------------------- |
| tools     | AI 自己判斷 | `@mcp.tool()`，參數來自 type hint                | `tools/list`                               | `tools/call {name, args}`  | `query_orders(date)`                      |
| resources | 應用程式/使用者挑給 AI 讀 | `@mcp.resource("uri")`，回傳字串或 bytes | `resources/list`、`resources/templates/list` | `resources/read {uri}`     | `pos://store/info`、`pos://orders/{date}` |
| prompts   | 使用者選    | `@mcp.prompt()`，回傳字串或 message 列表         | `prompts/list`                             | `prompts/get {name, args}` | `daily_report(date)`                      |

- tool 是「動作」，resource 是「資料」，prompt 是「提示詞樣板」。只有 tool 是 AI 主動決定呼叫；resource 和 prompt 在 Claude Code 裡分別對應 `@` 引用和 `/mcp__server__prompt` 指令。
- `@mcp.prompt()` 的 function 參數會變成 `prompts/list` 裡的 `arguments`，回傳純字串時 SDK 包成一則 `role: user` 的訊息。
- 三種能力 server 在 `initialize` 回應裡都會宣告（`capabilities.tools / resources / prompts`），**就算一個都沒註冊也會宣告**，list 只是回空陣列。所以「只看到 tool list」不是 server 不支援，而是沒註冊東西。

### resource 與 resource template 的差別

差別只在 URI 是固定的還是帶參數的。

|                | resource                                      | resource template                                            |
| -------------- | --------------------------------------------- | ------------------------------------------------------------ |
| 練習裡的例子   | `pos://store/info`                            | `pos://orders/{date}`                                        |
| server 端寫法  | `@mcp.resource("pos://store/info")`，function 不收參數 | `@mcp.resource("pos://orders/{date}")`，function 參數名要和 `{date}` 對上 |
| 列在哪         | `resources/list`                              | `resources/templates/list`                                   |
| 列出的欄位     | `uri`，是可以直接讀的實際位址                 | `uriTemplate`，是 RFC 6570 樣式，不是實際位址                |
| client 讀之前  | 直接用                                        | 自己把參數填進去，例如 `pos://orders/2026-11-08`             |
| 能讀出幾份     | 1 份                                          | 無限份，每個參數值一份                                       |
| 適合           | 數量有限、事先列得出來：設定檔、門市資料、固定文件 | 數量無限或動態：某天的訂單、某個使用者的資料、某個檔案路徑 |

- 兩者讀取都走同一個 `resources/read {uri}`。server 收到 template 的 URI 後比對樣式，抽出 `date="2026-11-08"` 丟給 function。
- template 不會出現在 `resources/list`，因為 server 不可能把每一個日期都列出來；client 要查 `resources/templates/list` 才知道有這個樣式。
- template 看起來很像有參數的 tool，差別在**誰決定要用**：tool 是 AI 看 description 自己決定呼叫；resource 和 template 是應用程式或使用者挑了塞給 AI 當上下文。在 Claude Code 打 `@pos-server:pos://orders/2026-11-08`，就是使用者主動把那天的訂單讀進對話，AI 不用自己呼叫。
- template 的參數可以搭配 `completion/complete` 做自動補全，使用者打到 `pos://orders/2026-11-` 時 server 回候選日期。這個練習沒做，流程圖第 3 區的 `completion/complete` 主要就是給 template 參數和 prompt 參數用的。

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
resource: pos://store/info | 門市基本資料
resource template: pos://orders/{date} | 某一天的訂單明細，date 格式 YYYY-MM-DD
read_resource: 2026-11-08 訂單明細：
#001 拿鐵 x2 $240
#002 可頌 x1 $80
prompt: daily_report | 產生某一天的營業日報 | args: ['date']
get_prompt: 請用 query_orders 查 2026-11-08 的營業資料，並讀取 pos://orders/2026-11-08，整理成一份營業日報。
```

### 兩種 transport

|           | stdio                                                                      | streamable-http                                                     |
| --------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| 怎麼連    | client 把 server 當子程序啟動，用 stdin/stdout 傳 JSON-RPC                 | server 常駐聽一個 port，client 用 URL 連                            |
| server 端 | `mcp.run()`                                                                | `mcp.run(transport="streamable-http", host="127.0.0.1", port=8123)` |
| client 端 | `Client(StdioServerParameters(command="python", args=["test-server.py"]))` | `Client("http://127.0.0.1:8123/mcp")`                               |
| session   | 一個子程序就是一個 session                                                 | 回應 header 帶 `mcp-session-id`，後續請求要帶回                     |
| 適合      | 本機工具，Claude Code / Desktop 預設                                       | 遠端或容器，正式版 `mcp-server/` 就是這種                           |

單獨跑 stdio 模式的 server 畫面會停住，那是在等 stdin，不是壞掉。

## JSON-RPC 流程圖

標 ★ 的是只註冊 tools 的最小 server 實際會用到的方法；這個練習多註冊了 resources 和 prompts，所以第 2、3 區的 resources/prompts 方法也會用到。

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
 │    resources/list ──────────────────────────────▶   固定 URI 的資料   │
 │    resources/templates/list ────────────────────▶   帶 {參數} 的 URI  │
 │    prompts/list ────────────────────────────────▶   提示範本          │
 └────────────────────────────────────────────────────────────────────────┘

 ┌─ 3. 使用：AI 決定要做什麼時 ──────────────────────────────────────────┐
 │  ★ tools/call {name, arguments} ────────────────▶                     │
 │  ◀──────────────────── result: content[] / structuredContent          │
 │    resources/read {uri} ────────────────────────▶                     │
 │    resources/subscribe / unsubscribe ───────────▶                     │
 │    prompts/get {name, arguments} ───────────────▶                     │
 │    completion/complete ─────────────────────────▶   template/prompt   │
 │                                                     參數自動補全      │
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

| 標準方法                 | test-client.py 裡的對應               |
| ------------------------ | ------------------------------------- |
| initialize + initialized | `async with Client(...)` 進入時自動做 |
| tools/list               | `client.list_tools()`                 |
| tools/call               | `client.call_tool(name, args)`        |
| resources/list           | `client.list_resources()`             |
| resources/templates/list | `client.list_resource_templates()`    |
| resources/read           | `client.read_resource(uri)`           |
| prompts/list             | `client.list_prompts()`               |
| prompts/get              | `client.get_prompt(name, args)`       |
| DELETE session           | 離開 `async with` 時自動做            |

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

**5. resources/list、resources/templates/list、resources/read**

```bash
curl -s http://127.0.0.1:8123/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "Mcp-Session-Id: $SID" \
  -d '{"jsonrpc":"2.0","id":4,"method":"resources/list"}'
# → {"resources":[{"name":"store_info","uri":"pos://store/info","mimeType":"text/plain",...}]}

curl -s http://127.0.0.1:8123/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "Mcp-Session-Id: $SID" \
  -d '{"jsonrpc":"2.0","id":5,"method":"resources/templates/list"}'
# → {"resourceTemplates":[{"name":"orders_by_date","uriTemplate":"pos://orders/{date}",...}]}

curl -s http://127.0.0.1:8123/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "Mcp-Session-Id: $SID" \
  -d '{"jsonrpc":"2.0","id":6,"method":"resources/read","params":{"uri":"pos://orders/2026-11-08"}}'
# → {"contents":[{"uri":"pos://orders/2026-11-08","mimeType":"text/plain","text":"2026-11-08 訂單明細：..."}]}
```

**6. prompts/list、prompts/get**

```bash
curl -s http://127.0.0.1:8123/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "Mcp-Session-Id: $SID" \
  -d '{"jsonrpc":"2.0","id":7,"method":"prompts/list"}'
# → {"prompts":[{"name":"daily_report","description":"產生某一天的營業日報","arguments":[{"name":"date","required":true}]}]}

curl -s http://127.0.0.1:8123/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "Mcp-Session-Id: $SID" \
  -d '{"jsonrpc":"2.0","id":8,"method":"prompts/get","params":{"name":"daily_report","arguments":{"date":"2026-11-08"}}}'
# → {"messages":[{"role":"user","content":{"type":"text","text":"請用 query_orders 查 2026-11-08 的營業資料，..."}}]}
```

**7. 結束 session**

```bash
curl -s -X DELETE http://127.0.0.1:8123/mcp -H "Mcp-Session-Id: $SID" -i
```

server 重啟後 session id 失效，會收到 404 或 session not found，重做第 1 步即可。
回應是 SSE 而不是純 JSON，是因為 POST 的回應可以串流，server 能先推進度再回結果。server 端設 `json_response=True` 就會改回 `application/json`，正式版 `mcp-server/server.py` 就是這樣。

## mcp 2.x 與網路教學的差異

網路上大多數教學還是 mcp 1.x，看到時把這幾個換掉即可：

| 1.x                                      | 2.x                                          |
| ---------------------------------------- | -------------------------------------------- |
| `from mcp.server.fastmcp import FastMCP` | `from mcp.server.mcpserver import MCPServer` |
| `tool.inputSchema`                       | `tool.input_schema`                          |
| `result.structuredContent`               | `result.structured_content`                  |
| `templates.resourceTemplates`            | `templates.resource_templates`               |
| `t.uriTemplate`                          | `t.uri_template`                             |

遷移說明：https://py.sdk.modelcontextprotocol.io/v2/migration/

## 下一步

- 把 `query_orders` 換成真的查資料（讀 JSON 檔或 SQLite），看 AI 怎麼用它。
- 幫 `pos://orders/{date}` 加 `completion/complete`，讓 client 打到一半就能列出有訂單的日期。
- 掛進 Claude Code 真的給 AI 用：`claude mcp add --transport http pos-server http://127.0.0.1:8123/mcp`，開新 session 問「11 月 8 日營業額多少」。打 `@pos-server:` 看 resource、打 `/mcp__pos-server__daily_report` 用 prompt。
- 回頭讀正式版 `mcp-server/server.py` 的 `build_http_app`：它多了 API key middleware、`stateless_http=True`，以及用環境變數切換 stdio / http。
