from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
 
# Initialize FastMCP server
mcp = FastMCP("weather-canada")
 
# Canadian Cities Coordinates
CANADIAN_CITIES = {
    "hamilton":   (43.2557, -79.8711),
    "toronto":    (43.6532, -79.3832),
    "ottawa":     (45.4215, -75.6972),
    "montreal":   (45.5017, -73.5673),
    "vancouver":  (49.2827, -123.1207),
    "calgary":    (51.0447, -114.0719),
    "edmonton":   (53.5461, -113.4938),
    "winnipeg":   (49.8951, -97.1384),
    "halifax":    (44.6488, -63.5752),
    "quebec":     (46.8139, -71.2080),
}
 
# Environment Canada alert region codes (LAYER:REGION format for CAP alerts)
CITY_ALERT_REGIONS = {
    "hamilton":   "ON/s0000582",
    "toronto":    "ON/s0000458",
    "ottawa":     "ON/s0000430",
    "montreal":   "QC/s0000635",
    "vancouver":  "BC/s0000141",
    "calgary":    "AB/s0000047",
    "edmonton":   "AB/s0000045",
    "winnipeg":   "MB/s0000193",
    "halifax":    "NS/s0000318",
    "quebec":     "QC/s0000620",
}
 
OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"
EC_ALERTS_BASE  = "https://dd.weather.gc.ca/alerts/cap"
 
# Weather code descriptions
WEATHER_CODES = {
    0:  "Clear sky ☀️",
    1:  "Mainly clear 🌤️",
    2:  "Partly cloudy ⛅",
    3:  "Overcast ☁️",
    45: "Foggy 🌫️",
    48: "Icy fog 🌫️",
    51: "Light drizzle 🌦️",
    53: "Moderate drizzle 🌦️",
    55: "Heavy drizzle 🌧️",
    61: "Slight rain 🌧️",
    63: "Moderate rain 🌧️",
    65: "Heavy rain 🌧️",
    71: "Slight snow 🌨️",
    73: "Moderate snow 🌨️",
    75: "Heavy snow ❄️",
    77: "Snow grains ❄️",
    80: "Slight showers 🌦️",
    81: "Moderate showers 🌧️",
    82: "Violent showers 🌧️",
    85: "Snow showers 🌨️",
    86: "Heavy snow showers ❄️",
    95: "Thunderstorm ⛈️",
    96: "Thunderstorm with hail ⛈️",
    99: "Thunderstorm with heavy hail ⛈️",
}
 
def get_weather_description(code: int) -> str:
    return WEATHER_CODES.get(code, "Unknown")
 
async def make_request(url: str, response_format: str = "json") -> Any | None:
    """Make an API request with error handling."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            if response_format == "text":
                return response.text
            return response.json()
        except Exception:
            return None
 
@mcp.tool()
async def get_canada_weather(city: str) -> str:
    """Get current weather and 7-day forecast for a Canadian city.
 
    Args:
        city: Canadian city name (e.g. hamilton, toronto, vancouver)
    """
    city_lower = city.lower().strip()
 
    # Look up coordinates
    if city_lower in CANADIAN_CITIES:
        lat, lon = CANADIAN_CITIES[city_lower]
    else:
        return (
            f"City '{city}' not found. "
            f"Available cities: {', '.join(CANADIAN_CITIES.keys())}"
        )
 
    url = (
        f"{OPEN_METEO_BASE}"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,apparent_temperature,"
        "weathercode,windspeed_10m,winddirection_10m,"
        "precipitation,relative_humidity_2m"
        "&daily=temperature_2m_max,temperature_2m_min,"
        "precipitation_sum,weathercode,windspeed_10m_max"
        "&timezone=America/Toronto"
        "&temperature_unit=celsius"
        "&windspeed_unit=kmh"
        "&precipitation_unit=mm"
    )
 
    data = await make_request(url)
    if not data:
        return "Unable to fetch weather data."
 
    current = data["current"]
    daily   = data["daily"]
 
    # Wind direction
    wind_deg = current.get("winddirection_10m", 0)
    directions = ["N","NE","E","SE","S","SW","W","NW"]
    wind_dir = directions[round(wind_deg / 45) % 8]
 
    result = f"""
🍁 {city.title()}, Canada — Current Weather
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Condition:      {get_weather_description(current['weathercode'])}
Temperature:    {current['temperature_2m']}°C
Feels Like:     {current['apparent_temperature']}°C
Humidity:       {current['relative_humidity_2m']}%
Wind:           {current['windspeed_10m']} km/h {wind_dir}
Precipitation:  {current['precipitation']} mm
 
📅 7-Day Forecast:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    for i in range(7):
        result += (
            f"{daily['time'][i]}  |  "
            f"{get_weather_description(daily['weathercode'][i])}  |  "
            f"High: {daily['temperature_2m_max'][i]}°C  "
            f"Low: {daily['temperature_2m_min'][i]}°C  |  "
            f"Rain: {daily['precipitation_sum'][i]}mm  |  "
            f"Wind: {daily['windspeed_10m_max'][i]}km/h\n"
        )
 
    return result
 
@mcp.tool()
async def get_canada_weather_by_coords(
    latitude: float,
    longitude: float
) -> str:
    """Get weather for any Canadian location by coordinates.
 
    Args:
        latitude:  Latitude of the location
        longitude: Longitude of the location
    """
    url = (
        f"{OPEN_METEO_BASE}"
        f"?latitude={latitude}&longitude={longitude}"
        "&current=temperature_2m,apparent_temperature,"
        "weathercode,windspeed_10m,precipitation,"
        "relative_humidity_2m"
        "&daily=temperature_2m_max,temperature_2m_min,"
        "precipitation_sum,weathercode"
        "&timezone=America/Toronto"
        "&temperature_unit=celsius"
        "&windspeed_unit=kmh"
    )
 
    data = await make_request(url)
    if not data:
        return "Unable to fetch weather data."
 
    current = data["current"]
    daily   = data["daily"]
 
    result = f"""
🍁 Location ({latitude}, {longitude}) — Current Weather
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Condition:      {get_weather_description(current['weathercode'])}
Temperature:    {current['temperature_2m']}°C
Feels Like:     {current['apparent_temperature']}°C
Humidity:       {current['relative_humidity_2m']}%
Wind:           {current['windspeed_10m']} km/h
Precipitation:  {current['precipitation']} mm
 
📅 7-Day Forecast:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    for i in range(7):
        result += (
            f"{daily['time'][i]}  |  "
            f"High: {daily['temperature_2m_max'][i]}°C  "
            f"Low: {daily['temperature_2m_min'][i]}°C  |  "
            f"Rain: {daily['precipitation_sum'][i]}mm\n"
        )
 
    return result
 
@mcp.tool()
async def get_canada_weather_alerts(city: str) -> str:
    """Get active weather alerts from Environment Canada for a Canadian city.
 
    Args:
        city: Canadian city name (e.g. hamilton, toronto, vancouver)
    """
    import xml.etree.ElementTree as ET
    from datetime import datetime, timezone
 
    city_lower = city.lower().strip()
 
    if city_lower not in CITY_ALERT_REGIONS:
        return (
            f"City '{city}' not found. "
            f"Available cities: {', '.join(CITY_ALERT_REGIONS.keys())}"
        )
 
    region_path = CITY_ALERT_REGIONS[city_lower]
    # Environment Canada CAP alerts index for the region
    alerts_url = f"{EC_ALERTS_BASE}/{region_path}.index"
 
    index_text = await make_request(alerts_url, response_format="text")
    if not index_text:
        # No index file means no active alerts
        return (
            f"⚠️ {city.title()}, Canada — Weather Alerts\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ No active weather alerts at this time."
        )
 
    # Parse alert file links from the index
    alert_files = [
        line.strip()
        for line in index_text.splitlines()
        if line.strip().endswith(".cap") or line.strip().endswith(".xml")
    ]
 
    if not alert_files:
        return (
            f"⚠️ {city.title()}, Canada — Weather Alerts\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ No active weather alerts at this time."
        )
 
    result = (
        f"⚠️ {city.title()}, Canada — Weather Alerts\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )
 
    parsed_count = 0
    for file_url in alert_files[:5]:  # limit to 5 most recent alerts
        cap_xml = await make_request(file_url, response_format="text")
        if not cap_xml:
            continue
 
        try:
            root = ET.fromstring(cap_xml)
            ns = {"cap": "urn:oasis:names:tc:emergency:cap:1.2"}
 
            # Extract alert fields
            status    = root.findtext("cap:status",   default="", namespaces=ns)
            msg_type  = root.findtext("cap:msgType",  default="", namespaces=ns)
            sent      = root.findtext("cap:sent",     default="", namespaces=ns)
 
            info = root.find("cap:info", namespaces=ns)
            if info is None:
                continue
 
            event      = info.findtext("cap:event",      default="Unknown event",  namespaces=ns)
            urgency    = info.findtext("cap:urgency",    default="Unknown",        namespaces=ns)
            severity   = info.findtext("cap:severity",   default="Unknown",        namespaces=ns)
            certainty  = info.findtext("cap:certainty",  default="Unknown",        namespaces=ns)
            headline   = info.findtext("cap:headline",   default="",               namespaces=ns)
            description= info.findtext("cap:description",default="",              namespaces=ns)
            effective  = info.findtext("cap:effective",  default="",               namespaces=ns)
            expires    = info.findtext("cap:expires",    default="",               namespaces=ns)
 
            # Skip cancelled or test alerts
            if status.lower() in ("test", "draft") or msg_type.lower() == "cancel":
                continue
 
            result += (
                f"\n🚨 {event}\n"
                f"   Headline:   {headline}\n"
                f"   Severity:   {severity}  |  Urgency: {urgency}  |  Certainty: {certainty}\n"
                f"   Effective:  {effective}\n"
                f"   Expires:    {expires}\n"
            )
            if description:
                # Trim long descriptions to first 300 chars
                short_desc = description.strip().replace("\n", " ")
                if len(short_desc) > 300:
                    short_desc = short_desc[:300] + "…"
                result += f"   Details:    {short_desc}\n"
 
            result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            parsed_count += 1
 
        except ET.ParseError:
            continue
 
    if parsed_count == 0:
        result += "✅ No active weather alerts at this time."
 
    return result
 
def main():
    mcp.run(transport="stdio")
 
if __name__ == "__main__":
    main()
 
# To quit Claude Desktop, use the command in PowerShell:
# Stop-Process -Name "claude" -Force -ErrorAction SilentlyContinue