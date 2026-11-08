import asyncio
from mcp.client.client import Client

async def main():
    async with Client("http://127.0.0.1:8123/mcp") as client:
        tools = await client.list_tools()
        for t in tools.tools:
            print("tool:", t.name, "|", t.description)
        result = await client.call_tool("query_orders", {"date": "2026-11-08"})
        print("result:", result.structured_content or result.content)

asyncio.run(main())