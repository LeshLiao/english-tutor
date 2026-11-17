from mcp.server.mcpserver import MCPServer

mcp = MCPServer("pos-server")

# ---------- tools：AI 可以「呼叫」的動作 ----------

@mcp.tool()
def query_orders(date: str) -> dict:
    """查詢某一天的訂單數量和營業額。date 格式為 YYYY-MM-DD。"""
    return {"date": date, "total": 128, "revenue": 35600}

@mcp.tool()
def query_today_date() -> dict:
    """查詢今天幾月幾號"""
    return {"date": "2026/11/08"}

# ---------- resources：AI 可以「讀取」的資料，用 URI 定位 ----------

@mcp.resource("pos://store/info", description="門市基本資料")
def store_info() -> str:
    """固定 URI 的 resource，會出現在 resources/list"""
    return "店名：微碧小舖\n地址：台中市西屯區\n營業時間：10:00-22:00"

@mcp.resource("pos://orders/{date}", description="某一天的訂單明細，date 格式 YYYY-MM-DD")
def orders_by_date(date: str) -> str:
    """URI 裡有 {參數} 的是 resource template，會出現在 resources/templates/list"""
    return f"{date} 訂單明細：\n#001 拿鐵 x2 $240\n#002 可頌 x1 $80"

# ---------- prompts：給 AI 用的提示詞樣板 ----------

@mcp.prompt(description="產生某一天的營業日報")
def daily_report(date: str) -> str:
    """回傳字串就是一則 user message；參數會變成 prompts/list 裡的 arguments"""
    return f"請用 query_orders 查 {date} 的營業資料，並讀取 pos://orders/{date}，整理成一份營業日報。"

if __name__ == "__main__":
    print("Start mcp server…")
    #mcp.run()  # 預設 transport="stdio"：用 stdin/stdout 跟 client 講 JSON-RPC

    mcp.run(transport="streamable-http", host="127.0.0.1", port=8123)
