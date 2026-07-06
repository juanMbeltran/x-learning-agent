"""
Deterministic wrapper around the Zernio API.

Every function here is pure I/O — same input always produces the same
network call. No judgment, no AI. This is intentionally boring.

Zernio docs: https://docs.zernio.com/
Base URL:    https://zernio.com/api/v1
Auth:        Authorization: Bearer <ZERNIO_API_KEY>
"""

import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://zernio.com/api/v1"


def _headers() -> dict:
    api_key = os.getenv("ZERNIO_API_KEY")
    if not api_key:
        raise EnvironmentError("ZERNIO_API_KEY is not set.")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _account_id() -> str:
    account_id = os.getenv("ZERNIO_ACCOUNT_ID")
    if not account_id:
        raise EnvironmentError(
            "ZERNIO_ACCOUNT_ID is not set. Run `python tools/get_account_id.py` to find it."
        )
    return account_id


# ---------------------------------------------------------------------------
# Account helpers
# ---------------------------------------------------------------------------

def list_accounts() -> list[dict]:
    """
    Return all social accounts connected to this Zernio API key.
    Use this once to find your Twitter account ID.
    """
    response = requests.get(f"{BASE_URL}/accounts", headers=_headers())
    response.raise_for_status()
    return response.json().get("accounts", [])


# ---------------------------------------------------------------------------
# Posting
# ---------------------------------------------------------------------------

def post_tweet(text: str) -> dict:
    """
    Publish a tweet immediately via Zernio.

    Returns:
        { "post_id": str, "text": str, "posted_at": str (ISO 8601) }
    """
    if len(text) > 280:
        raise ValueError(f"Tweet is {len(text)} chars — exceeds 280 char limit.")

    body = {
        "content": text,
        "publishNow": True,
        "platforms": [
            {"platform": "twitter", "accountId": _account_id()}
        ],
    }

    response = requests.post(f"{BASE_URL}/posts", headers=_headers(), json=body)
    response.raise_for_status()
    post = response.json().get("post", {})

    return {
        "post_id": post["_id"],
        "text": text,
        "posted_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

def get_post_metrics(post_id: str) -> dict:
    """
    Fetch engagement metrics for a single post.

    Returns:
        {
            "post_id": str,
            "likes": int,
            "retweets": int,
            "replies": int,
            "impressions": int,
            "fetched_at": str (ISO 8601)
        }
    """
    response = requests.get(
        f"{BASE_URL}/analytics",
        headers=_headers(),
        params={"postId": post_id},
    )
    response.raise_for_status()
    analytics = response.json().get("analytics", {})

    return {
        "post_id": post_id,
        "likes": analytics.get("likes", 0),
        "retweets": analytics.get("shares", 0),
        "replies": analytics.get("comments", 0),
        "impressions": analytics.get("impressions", 0),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def get_recent_posts_metrics(limit: int = 20) -> list[dict]:
    """
    Fetch the most recent posts with their metrics from Zernio.
    Useful for the learner agent to get a full picture.

    Returns a list of dicts with post content + engagement numbers.
    """
    response = requests.get(
        f"{BASE_URL}/analytics/posts",
        headers=_headers(),
        params={"limit": limit},
    )
    response.raise_for_status()
    posts = response.json().get("posts", [])

    return [
        {
            "post_id": p.get("_id", ""),
            "text": p.get("content", ""),
            "posted_at": p.get("scheduledFor") or p.get("createdAt", ""),
            "likes": p.get("likes", 0),
            "retweets": p.get("shares", 0),
            "replies": p.get("comments", 0),
            "impressions": p.get("impressions", 0),
        }
        for p in posts
    ]
