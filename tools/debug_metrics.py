#!/usr/bin/env python3
"""Run once to inspect the raw Zernio analytics API response."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://zernio.com/api/v1"
api_key = os.getenv("ZERNIO_API_KEY")
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

# Use a real post_id from your post_history.json
POST_ID = "6a477a26649f7902e4edb6a0"

response = requests.get(f"{BASE_URL}/analytics", headers=headers, params={"postId": POST_ID})
print(f"Status: {response.status_code}")
print("Raw response:")
print(json.dumps(response.json(), indent=2))
