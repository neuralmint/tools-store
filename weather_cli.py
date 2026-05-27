#!/usr/bin/env python3
"""
weather_cli.py — Current weather for any city using wttr.in free API.

Usage:
    python weather_cli.py <city>
    python weather_cli.py <city> --forecast
    python weather_cli.py <city> --json
    python weather_cli.py <city> --forecast --json
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse

CACHE_FILE = os.path.expanduser("~/.cache/weather_cli_cache.json")
CACHE_TTL = 300  # 5 minutes


def load_cache():
    """Load cached weather data, returns {} if missing/expired."""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    # Remove expired entries
    now = time.time()
    return {k: v for k, v in data.items() if v.get("_ts", 0) + CACHE_TTL > now}


def save_cache(cache):
    """Persist cache to disk."""
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


def fetch_weather(city, forecast=False):
    """Fetch weather data from wttr.in API."""
    cache_key = f"{city.lower().strip()}:{'forecast' if forecast else 'current'}"
    cache = load_cache()
    if cache_key in cache:
        return cache[cache_key]["data"], True

    # Build URL
    params = {
        "format": "%C|%t|%f|%h|%w|%p|%l",
    }
    if forecast:
        url = f"https://wttr.in/{urllib.parse.quote(city.strip())}?0pqT"
    else:
        url = f"https://wttr.in/{urllib.parse.quote(city.strip())}?format=%C|%t|%f|%h|%w|%p|%l"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.88.1"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8").strip()
    except urllib.error.HTTPError as e:
        sys.exit(f"Error: API returned HTTP {e.code} for '{city}'")
    except urllib.error.URLError as e:
        sys.exit(f"Error: Could not reach wttr.in: {e.reason}")

    if forecast:
        data = parse_forecast(raw)
    else:
        data = parse_current(raw, city)

    # Cache it
    cache[cache_key] = {"data": data, "_ts": time.time()}
    save_cache(cache)
    return data, False


def parse_current(raw, city):
    """Parse simple format output: conditions|temp|feels|humidity|wind|precip|location"""
    parts = raw.split("|")
    if len(parts) < 6:
        return {"city": city, "error": f"Unexpected response format: {raw[:100]}"}

    conditions = parts[0].strip()
    temp_str = parts[1].strip()
    feels_like = parts[2].strip()
    humidity_str = parts[3].strip()
    wind_str = parts[4].strip()
    precip_str = parts[5].strip()
    location = parts[6].strip() if len(parts) > 6 else city

    return {
        "city": location,
        "conditions": conditions,
        "temperature": temp_str,
        "feels_like": feels_like,
        "humidity": humidity_str,
        "wind": wind_str,
        "precipitation": precip_str,
    }


def parse_forecast(raw):
    """Parse the multi-line forecast output from wttr.in with ?0pqT format."""
    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    if not lines:
        return {"error": "No forecast data received"}

    # wttr.in forecast format varies; return raw text for display
    return {"raw_forecast": raw, "lines": lines}


def format_output(data, json_output, forecast):
    """Format weather data for display."""
    if json_output:
        return json.dumps(data, indent=2)

    if "error" in data:
        return f"⚠️  {data['error']}"

    if forecast and "raw_forecast" in data:
        return data["raw_forecast"]

    lines = []
    lines.append(f"Weather for {data.get('city', 'Unknown')}")
    lines.append("-" * 40)
    lines.append(f"  Conditions:    {data.get('conditions', 'N/A')}")
    lines.append(f"  Temperature:   {data.get('temperature', 'N/A')}")
    lines.append(f"  Feels like:    {data.get('feels_like', 'N/A')}")
    lines.append(f"  Humidity:      {data.get('humidity', 'N/A')}")
    lines.append(f"  Wind:          {data.get('wind', 'N/A')}")
    lines.append(f"  Precipitation: {data.get('precipitation', 'N/A')}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Get current weather for any city.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  weather_cli.py London\n"
            "  weather_cli.py Tokyo --forecast\n"
            "  weather_cli.py Paris --json\n"
            "  weather_cli.py New\\ York --forecast --json\n"
        ),
    )
    parser.add_argument("city", help="City name (e.g., London, Tokyo, New York)")
    parser.add_argument("--forecast", action="store_true", help="Show 3-day forecast")
    parser.add_argument("--json", action="store_true", dest="json_flag", help="Output as JSON")
    args = parser.parse_args()

    data, from_cache = fetch_weather(args.city, forecast=args.forecast)
    output = format_output(data, args.json_flag, args.forecast)
    print(output)


if __name__ == "__main__":
    main()
