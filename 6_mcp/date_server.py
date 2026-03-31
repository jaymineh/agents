import sys
from datetime import date
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("date_server")

@mcp.tool()
async def get_current_date() -> str:
    """Return today's date in ISO format (YYYY-MM-DD).

    Use this tool whenever you need to know the current date.
    """
    return date.today().isoformat()

if __name__ == "__main__":
    transport = "sse" if "--sse" in sys.argv else "stdio"
    mcp.run(transport=transport)
