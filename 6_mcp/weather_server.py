import sys
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather_server")


@mcp.tool()
async def get_current_weather(city: str) -> str:
    """Get the current weather for a city using the free Open-Meteo API.
    No API key required.

    Args:
        city: The name of the city to get weather for
    """
    async with httpx.AsyncClient() as client:
        geo = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
        )
        geo_data = geo.json()

        if not geo_data.get("results"):
            return f"Could not find location: {city}"

        loc = geo_data["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]
        name = f"{loc['name']}, {loc.get('country', '')}"

        weather = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                "temperature_unit": "celsius",
            },
        )
        w = weather.json()["current"]

    return (
        f"Weather in {name}: "
        f"{w['temperature_2m']}°C, "
        f"Humidity: {w['relative_humidity_2m']}%, "
        f"Wind: {w['wind_speed_10m']} km/h"
    )


if __name__ == "__main__":
    transport = "sse" if "--sse" in sys.argv else "stdio"
    mcp.run(transport=transport)
