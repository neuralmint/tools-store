#!/usr/bin/env python3
"""
currency_converter.py — Real-time currency conversion using free API.

Uses exchangerate-api.com free tier (no API key required for basic usage).

Usage:
    python currency_converter.py --from USD --to EUR --amount 100
    python currency_converter.py --list
    python currency_converter.py --from GBP --to JPY --amount 50 --json
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse

API_BASE = "https://open.er-api.com/v6"
CACHE_FILE = os.path.expanduser("~/.cache/currency_cache.json")
CACHE_TTL = 3600  # 1 hour


# Built-in common currencies (used when API is unreachable for --list)
FALLBACK_CURRENCIES = {
    "USD": "United States Dollar",
    "EUR": "Euro",
    "GBP": "British Pound Sterling",
    "JPY": "Japanese Yen",
    "AUD": "Australian Dollar",
    "CAD": "Canadian Dollar",
    "CHF": "Swiss Franc",
    "CNY": "Chinese Yuan",
    "INR": "Indian Rupee",
    "BRL": "Brazilian Real",
    "MXN": "Mexican Peso",
    "KRW": "South Korean Won",
    "SGD": "Singapore Dollar",
    "HKD": "Hong Kong Dollar",
    "NZD": "New Zealand Dollar",
    "SEK": "Swedish Krona",
    "NOK": "Norwegian Krone",
    "TRY": "Turkish Lira",
    "ZAR": "South African Rand",
    "RUB": "Russian Ruble",
    "PLN": "Polish Zloty",
    "THB": "Thai Baht",
    "DKK": "Danish Krone",
    "CZK": "Czech Koruna",
    "ILS": "Israeli Shekel",
    "AED": "UAE Dirham",
    "SAR": "Saudi Riyal",
    "ARS": "Argentine Peso",
    "CLP": "Chilean Peso",
    "PHP": "Philippine Peso",
    "MYR": "Malaysian Ringgit",
    "IDR": "Indonesian Rupiah",
    "VND": "Vietnamese Dong",
    "NGN": "Nigerian Naira",
    "EGP": "Egyptian Pound",
    "PKR": "Pakistani Rupee",
    "BDT": "Bangladeshi Taka",
    "TWD": "Taiwan Dollar",
}


def load_cache():
    """Load cached exchange rate data."""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    now = time.time()
    return {k: v for k, v in data.items() if v.get("_ts", 0) + CACHE_TTL > now}


def save_cache(cache):
    """Persist cache to disk."""
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


def api_get(path):
    """Make a GET request to the exchange rate API."""
    url = f"{API_BASE}{path}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "currency_converter/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit(f"API error: HTTP {e.code} - {e.read().decode('utf-8', errors='replace')}")
    except urllib.error.URLError as e:
        sys.exit(f"Network error: {e.reason}")
    except json.JSONDecodeError:
        sys.exit("Error: Invalid JSON response from API")


def get_currencies_from_api():
    """Get currency list by fetching latest rates and extracting keys."""
    cache = load_cache()
    if "currencies_list" in cache:
        return cache["currencies_list"]["data"]

    data = api_get("/latest/USD")
    rates = data.get("rates", {})
    currency_codes = set(rates.keys())

    # Build a dictionary from our fallback + any codes we don't have names for
    result = {}
    for code in sorted(currency_codes):
        if code in FALLBACK_CURRENCIES:
            result[code] = FALLBACK_CURRENCIES[code]
        else:
            result[code] = code  # just show the code if we don't have the name

    cache["currencies_list"] = {"data": result, "_ts": time.time()}
    save_cache(cache)
    return result


def convert_currency(from_currency, to_currency, amount):
    """Convert an amount from one currency to another."""
    cache_key = f"rate:{from_currency.upper()}:{to_currency.upper()}"
    cache = load_cache()
    if cache_key in cache:
        rate = cache[cache_key]["data"]
        converted = round(amount * rate, 2)
        return {"rate": rate, "result": converted, "cached": True}

    # Fetch latest rates for the source currency
    data = api_get(f"/latest/{from_currency.upper()}")
    rates = data.get("rates", {})
    if to_currency.upper() not in rates:
        sys.exit(f"Error: Could not convert {from_currency} -> {to_currency}")

    rate = rates[to_currency.upper()]
    converted = round(amount * rate, 2)

    # Cache the rate
    cache[cache_key] = {"data": rate, "_ts": time.time()}
    save_cache(cache)

    return {
        "rate": rate,
        "result": converted,
        "date": data.get("time_last_update_utc", ""),
        "cached": False,
    }


def format_output(result_data, from_cur, to_cur, amount, json_output, currencies=None):
    """Format conversion or currency list for display."""
    if currencies is not None:
        if json_output:
            return json.dumps(currencies, indent=2)

        lines = ["Available currencies:", ""]
        for code, name in sorted(currencies.items()):
            lines.append(f"  {code:>4}  —  {name}")
        return "\n".join(lines)

    if json_output:
        output = {
            "from": from_cur.upper(),
            "to": to_cur.upper(),
            "amount": amount,
            "rate": result_data["rate"],
            "result": result_data["result"],
        }
        if not result_data.get("cached"):
            output["date"] = result_data.get("date", "")
        return json.dumps(output, indent=2)

    lines = []
    lines.append(f"{amount:.2f} {from_cur.upper()}  =  {result_data['result']:.2f} {to_cur.upper()}")
    lines.append(f"  Rate: 1 {from_cur.upper()} = {result_data['rate']:.6f} {to_cur.upper()}")
    if not result_data.get("cached"):
        lines.append(f"  Date: {result_data.get('date', 'latest')}")
    else:
        lines.append(f"  (cached rate)")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Real-time currency converter (free API, no API key required).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  currency_converter.py --from USD --to EUR --amount 100\n"
            "  currency_converter.py --list\n"
            "  currency_converter.py --from GBP --to JPY --amount 50 --json\n"
        ),
    )
    parser.add_argument("--from", dest="from_cur", help="Source currency code (e.g., USD)")
    parser.add_argument("--to", dest="to_cur", help="Target currency code (e.g., EUR)")
    parser.add_argument("--amount", type=float, default=1.0, help="Amount to convert (default: 1)")
    parser.add_argument("--list", action="store_true", help="List all available currencies")
    parser.add_argument("--json", action="store_true", dest="json_flag", help="Output as JSON")
    args = parser.parse_args()

    if args.list:
        currencies = get_currencies_from_api()
        print(format_output(None, None, None, None, args.json_flag, currencies=currencies))
        return

    if not args.from_cur or not args.to_cur:
        parser.print_help()
        print("\nError: --from and --to are required unless using --list")
        sys.exit(1)

    result = convert_currency(args.from_cur, args.to_cur, args.amount)
    print(format_output(result, args.from_cur, args.to_cur, args.amount, args.json_flag))


if __name__ == "__main__":
    main()
