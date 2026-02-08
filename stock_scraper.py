import os
import json
import time
import requests
from dateutil import parser as dtparser
from dotenv import load_dotenv

load_dotenv()  # Load env vars from .env file (if it exists)

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
if not SERPAPI_KEY:
    raise RuntimeError("Missing SERPAPI_KEY env var (set SERPAPI_KEY='...').")

SERPAPI_URL = "https://serpapi.com/search.json"

STOCKS = [
    {"name": "The Trade Desk", "ticker": "TTD", "q": "TTD:NASDAQ"},
    {"name": "Bumble", "ticker": "BMBL", "q": "BMBL:NASDAQ"},
    {"name": "Capital One", "ticker": "COF", "q": "COF:NYSE"},
    {"name": "DraftKings", "ticker": "DKNG", "q": "DKNG:NASDAQ"},
    {"name": "Chevron", "ticker": "CVX", "q": "CVX:NYSE"},
    {"name": "Roblox", "ticker": "RBLX", "q": "RBLX:NYSE"},
    {"name": "Coinbase", "ticker": "COIN", "q": "COIN:NASDAQ"},
    {"name": "JP Morgan", "ticker": "JPM", "q": "JPM:NYSE"},
    {"name": "Spotify", "ticker": "SPOT", "q": "SPOT:NYSE"},
    {"name": "Walmart", "ticker": "WMT", "q": "WMT:NASDAQ"},
]

def fetch_graph(q: str, window: str = "1Y", hl: str = "en", retries: int = 3):
    params = {
        "engine": "google_finance",
        "q": q,
        "window": window,
        "hl": hl,
        "api_key": SERPAPI_KEY,
        # Optional smaller payload:
        # "json_restrictor": "graph",
    }

    last_err = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(SERPAPI_URL, params=params, timeout=60)
            r.raise_for_status()
            data = r.json()

            if "error" in data:
                raise RuntimeError(f"SerpApi error: {data['error']}")

            graph = data.get("graph")
            if not isinstance(graph, list):
                raise RuntimeError(f"No graph array returned for {q}. Keys: {list(data.keys())}")

            return graph
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(1.0 * attempt)
            else:
                raise last_err

def to_yyyy_mm_dd(date_str: str):
    if not date_str:
        return None
    try:
        return dtparser.parse(date_str).date().isoformat()
    except Exception:
        return date_str  # fallback if parsing fails

flat = []
failures = []

for s in STOCKS:
    try:
        graph = fetch_graph(s["q"], window="1Y")

        # IMPORTANT: preserve the order returned by SerpApi (do not sort)
        for p in graph:
            flat.append({
                "ticker": s["ticker"],
                "date": to_yyyy_mm_dd(p.get("date")),
                "price": p.get("price"),
            })

        print(f"OK: {s['q']} ({len(graph)} points)")
        time.sleep(0.25)  # light throttle
    except Exception as e:
        failures.append({"ticker": s["ticker"], "q": s["q"], "error": str(e)})
        print(f"FAILED: {s['q']} -> {e}")

with open("stocks_daily_prices.json", "w", encoding="utf-8") as f:
    json.dump(flat, f, indent=2, ensure_ascii=False)

print("\nSaved: stocks_daily_prices.json")

if failures:
    with open("ten_stocks_failures.json", "w", encoding="utf-8") as f:
        json.dump(failures, f, indent=2, ensure_ascii=False)
    print("Saved failures: ten_stocks_failures.json")
