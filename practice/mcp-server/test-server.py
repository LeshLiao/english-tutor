from mcp.server.mcpserver import MCPServer

mcp = MCPServer("pos-server")

@mcp.tool()
def query_orders(date: str) -> dict:
    """查詢某一天的訂單數量和營業額。date 格式為 YYYY-MM-DD。"""
    return {"date": date, "total": 128, "revenue": 35600}

@mcp.tool()
def query_today_date() -> dict:
    """查詢今天幾月幾號"""
    return {"date": "2026/11/08"}

if __name__ == "__main__":
    print("Start mcp server…")
    #mcp.run()  # 預設 transport="stdio"：用 stdin/stdout 跟 client 講 JSON-RPC

    mcp.run(transport="streamable-http", host="127.0.0.1", port=8123)