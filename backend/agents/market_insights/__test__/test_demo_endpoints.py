#!/usr/bin/env python3
"""Quick test to verify which endpoints work with Demo API."""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("COINGECKO_API_KEY")
if not API_KEY:
    print("❌ COINGECKO_API_KEY not set!")
    exit(1)

BASE = "https://api.coingecko.com/api/v3/onchain"
HEADERS = {"x-cg-demo-api-key": API_KEY}

tests = [
    ("Pool Data", f"{BASE}/networks/eth/pools/0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", {"x_cg_demo_api_key": API_KEY}),
    ("Token Data", f"{BASE}/networks/eth/tokens/0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", {"x_cg_demo_api_key": API_KEY, "include": "top_pools"}),
    ("Token Top Pools", f"{BASE}/networks/eth/tokens/0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2/pools", {"x_cg_demo_api_key": API_KEY}),
    ("Simple Token Price", f"{BASE}/simple/networks/eth/token_price/0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", {"x_cg_demo_api_key": API_KEY}),
    ("Trending Pools (All)", f"{BASE}/networks/trending_pools", {"x_cg_demo_api_key": API_KEY, "page": 1}),
    ("Trending Pools (ETH)", f"{BASE}/networks/eth/trending_pools", {"x_cg_demo_api_key": API_KEY, "page": 1}),
    ("Trending Pools (Polygon)", f"{BASE}/networks/polygon/trending_pools", {"x_cg_demo_api_key": API_KEY, "page": 1}),
]

print("🧪 Testing CoinGecko Demo API Endpoints\n")
print("=" * 70)

results = []
for name, url, params in tests:
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            count = len(data.get("data", [])) if isinstance(data.get("data"), list) else "N/A"
            print(f"✅ {name:30} - Status: {r.status_code} - Items: {count}")
            results.append((name, True))
        else:
            error = r.json().get("status", {}).get("error_message", r.text[:100]) if r.headers.get('content-type', '').startswith('application/json') else r.text[:100]
            print(f"❌ {name:30} - Status: {r.status_code} - {error}")
            results.append((name, False))
    except Exception as e:
        print(f"❌ {name:30} - ERROR: {str(e)[:100]}")
        results.append((name, False))

print("\n" + "=" * 70)
working = [n for n, w in results if w]
not_working = [n for n, w in results if not w]
print(f"✅ Working: {len(working)}/{len(results)}")
if working:
    print("   " + ", ".join(working))
if not_working:
    print(f"\n❌ Not Working: {len(not_working)}/{len(results)}")
    print("   " + ", ".join(not_working))

