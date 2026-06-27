"""
Run this once to find your Twitter account ID on Zernio.
Copy the _id value into your .env as ZERNIO_ACCOUNT_ID.

Usage:
    python tools/get_account_id.py
"""

from x_client import list_accounts

accounts = list_accounts()

if not accounts:
    print("No accounts found. Make sure your X account is connected in Zernio.")
else:
    for acc in accounts:
        print(f"Platform : {acc.get('platform')}")
        print(f"Username : {acc.get('username')}")
        print(f"ID       : {acc.get('_id')}")
        print("---")
