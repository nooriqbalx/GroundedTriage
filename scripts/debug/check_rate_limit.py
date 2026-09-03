"""
SecuriCopilot -- Check if we're being rate-limited
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
HYBRID_ANALYSIS_KEY = os.getenv("HYBRID_ANALYSIS_API_KEY")

# A hash we KNOW has a real report, confirmed earlier
known_good_hash = "ef88d67603efeb33fc269bf6c924ad1afbaf2c36099a7b5247a1bca171b15a6a"

headers = {"api-key": HYBRID_ANALYSIS_KEY, "user-agent": "Falcon Sandbox"}
url = "https://www.hybrid-analysis.com/api/v2/search/hash"

resp = requests.post(url, headers=headers, params={"hash": known_good_hash}, timeout=30)

print(f"Status code: {resp.status_code}")
print(f"Headers: {dict(resp.headers)}")
print(f"Body: {resp.text[:500]}")