import json
import mcp
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

params = StdioServerParameters(command="uv", args=["run", "date_server.py"], env=None)


async def list_date_tools():
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            return tools_result.tools


async def call_date_tool(tool_name: str, tool_args: dict) -> str:
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, tool_args)
            return result.content[0].text


async def get_date_tools_openai_format() -> list[dict]:
    """Return tools in the format expected by the native OpenAI API."""
    tools = []
    for tool in await list_date_tools():
        tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {**tool.inputSchema, "additionalProperties": False},
                "strict": True,
            },
        })
    return tools
