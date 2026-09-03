"""
SecuriCopilot -- Debug the search/hash call, trying JSON body instead of form data
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
HYBRID_ANALYSIS_KEY = os.getenv("HYBRID_ANALYSIS_API_KEY")

sha256 = "00c4603f074afb652780bb8b3e703ae093c5644652b81954ec6d0fb983e79203"

headers = {
    "api-key": HYBRID_ANALYSIS_KEY,
    "user-agent": "Falcon Sandbox",
    "accept": "application/json",
}

url = "https://www.hybrid-analysis.com/api/v2/search/hash"

print("--- Attempt 1: JSON body ---")
resp = requests.post(url, headers=headers, json={"hash": sha256}, timeout=30)
print(f"Status: {resp.status_code}")
print(f"Body: {resp.text[:500]}\n")

print("--- Attempt 2: form data with explicit content-type ---")
headers2 = dict(headers)
headers2["content-type"] = "application/x-www-form-urlencoded"
resp2 = requests.post(url, headers=headers2, data=f"hash={sha256}", timeout=30)
print(f"Status: {resp2.status_code}")
print(f"Body: {resp2.text[:500]}\n")

print("--- Attempt 3: as query parameter ---")
resp3 = requests.post(url, headers=headers, params={"hash": sha256}, timeout=30)
print(f"Status: {resp3.status_code}")
print(f"Body: {resp3.text[:500]}")