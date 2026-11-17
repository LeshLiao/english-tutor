import asyncio
from mcp.client.client import Client

async def main():
    async with Client("http://127.0.0.1:8123/mcp") as client:
        tools = await client.list_tools()
        for t in tools.tools:
            print("tool:", t.name, "|", t.description)
        result = await client.call_tool("query_orders", {"date": "2026-11-08"})
        print("result:", result.structured_content or result.content)

        resources = await client.list_resources()
        for r in resources.resources:
            print("resource:", r.uri, "|", r.description)
        templates = await client.list_resource_templates()
        for t in templates.resource_templates:
            print("resource template:", t.uri_template, "|", t.description)
        content = await client.read_resource("pos://orders/2026-11-08")
        print("read_resource:", content.contents[0].text)

        prompts = await client.list_prompts()
        for p in prompts.prompts:
            print("prompt:", p.name, "|", p.description, "| args:", [a.name for a in p.arguments or []])
        prompt = await client.get_prompt("daily_report", {"date": "2026-11-08"})
        print("get_prompt:", prompt.messages[0].content.text)

asyncio.run(main())
