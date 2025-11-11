"""
Quick test script to check which CoinGecko API endpoints work with Demo API.
Run this to see which endpoints are available.
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

load_dotenv()

API_KEY = os.getenv("COINGECKO_API_KEY", "")
BASE_URL = "https://api.coingecko.com/api/v3/onchain"

if not API_KEY:
    print("❌ COINGECKO_API_KEY not set!")
    print("   Set it in .env file: COINGECKO_API_KEY=your_key_here")
    sys.exit(1)

print(f"🔑 Testing with API key: {API_KEY[:10]}...")
print(f"🌐 Base URL: {BASE_URL}\n")

# Test endpoints
test_cases = [
    {
        "name": "Pool Data (ETH pool)",
        "endpoint": "networks/eth/pools/0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        "params": {"x_cg_demo_api_key": API_KEY},
    },
    {
        "name": "Token Data (WETH)",
        "endpoint": "networks/eth/tokens/0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "params": {"x_cg_demo_api_key": API_KEY, "include": "top_pools"},
    },
    {
        "name": "Token Top Pools (WETH)",
        "endpoint": "networks/eth/tokens/0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2/pools",
        "params": {"x_cg_demo_api_key": API_KEY},
    },
    {
        "name": "Trending Pools (All Networks)",
        "endpoint": "networks/trending_pools",
        "params": {"x_cg_demo_api_key": API_KEY, "page": 1, "duration": "24h"},
    },
    {
        "name": "Trending Pools (Ethereum)",
        "endpoint": "networks/eth/trending_pools",
        "params": {"x_cg_demo_api_key": API_KEY, "page": 1, "duration": "24h"},
    },
    {
        "name": "Trending Pools (Polygon)",
        "endpoint": "networks/polygon/trending_pools",
        "params": {"x_cg_demo_api_key": API_KEY, "page": 1, "duration": "24h"},
    },
    {
        "name": "Trending Search Pools",
        "endpoint": "pools/trending_search",
        "params": {"x_cg_demo_api_key": API_KEY},
    },
]

results = []

for test in test_cases:
    url = f"{BASE_URL}/{test['endpoint']}"
    headers = {"x-cg-demo-api-key": API_KEY}
    
    print(f"🧪 Testing: {test['name']}")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, params=test['params'], timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                count = len(data.get("data", []))
                print(f"   ✅ SUCCESS - Got {count} items")
                results.append((test['name'], True, None))
            else:
                print(f"   ✅ SUCCESS - Response received")
                results.append((test['name'], True, None))
        elif response.status_code == 401:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_msg = error_data.get('status', {}).get('error_message', 'Unauthorized')
            print(f"   ❌ FAILED - 401 Unauthorized: {error_msg}")
            results.append((test['name'], False, "401: " + error_msg))
        elif response.status_code == 404:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_msg = error_data.get('status', {}).get('error_message', 'Not Found')
            print(f"   ❌ FAILED - 404 Not Found: {error_msg}")
            results.append((test['name'], False, "404: " + error_msg))
        else:
            print(f"   ❌ FAILED - {response.status_code}: {response.text[:200]}")
            results.append((test['name'], False, f"{response.status_code}: {response.text[:100]}"))
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        results.append((test['name'], False, str(e)))
    
    print()

# Summary
print("=" * 70)
print("📊 SUMMARY")
print("=" * 70)
working = []
not_working = []

for name, works, error in results:
    if works:
        working.append(name)
        print(f"✅ {name}")
    else:
        not_working.append((name, error))
        print(f"❌ {name}: {error}")

print(f"\n✅ {len(working)}/{len(results)} endpoints work")
print(f"❌ {len(not_working)}/{len(results)} endpoints don't work")

if not_working:
    print("\n⚠️  Endpoints that don't work (may require paid plan):")
    for name, error in not_working:
        print(f"   - {name}: {error}")

