"""
Deterministic file I/O — reads and writes the two persistence files:

  learnings.md       — the agent's evolving knowledge base (plain text/markdown)
  post_history.json  — log of every post + its latest metrics

Nothing in this file makes decisions. It just moves data in and out of disk.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# DATA_DIR can be overridden by the DATA_DIR env var.
# On Render, set DATA_DIR=/data (the persistent disk mount point).
# Locally it defaults to the project root so nothing changes.
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR))
DATA_DIR.mkdir(parents=True, exist_ok=True)

LEARNINGS_FILE = DATA_DIR / "learnings.md"
HISTORY_FILE = DATA_DIR / "post_history.json"


# ---------------------------------------------------------------------------
# learnings.md
# ---------------------------------------------------------------------------

def read_learnings() -> str:
    """Return the full contents of learnings.md, or an empty string if it doesn't exist."""
    if not LEARNINGS_FILE.exists():
        return ""
    return LEARNINGS_FILE.read_text(encoding="utf-8")


def write_learnings(content: str) -> None:
    """Overwrite learnings.md with new content."""
    LEARNINGS_FILE.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# post_history.json
# ---------------------------------------------------------------------------

def _load_raw() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    with HISTORY_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def _save_raw(data: list[dict]) -> None:
    with HISTORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def log_post(post_id: str, text: str, posted_at: str) -> None:
    """
    Append a new post entry to post_history.json.

    Each entry starts with zero metrics; they get filled in later by the
    metrics collector.
    """
    history = _load_raw()
    history.append({
        "post_id": post_id,
        "text": text,
        "posted_at": posted_at,
        "metrics": {
            "likes": 0,
            "retweets": 0,
            "replies": 0,
            "impressions": 0,
            "last_fetched": None,
        },
    })
    _save_raw(history)


def update_post_metrics(post_id: str, metrics: dict) -> None:
    """
    Find the post with the given post_id and update its metrics in place.

    metrics dict should contain: likes, retweets, replies, impressions.
    """
    history = _load_raw()
    for entry in history:
        if entry["post_id"] == post_id:
            entry["metrics"].update(metrics)
            entry["metrics"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
            break
    _save_raw(history)


def load_post_history() -> list[dict]:
    """Return the full post history, newest first."""
    history = _load_raw()
    return sorted(history, key=lambda p: p["posted_at"], reverse=True)


def get_recent_posts(count: int = 10) -> list[dict]:
    """Return the N most recent posts (text + metrics)."""
    return load_post_history()[:count]


def get_posts_older_than_hours(hours: int = 1) -> list[dict]:
    """
    Return posts that are at least `hours` old.

    Useful for the metrics collector — you want to give X time to accumulate
    engagement before fetching metrics (fetching immediately after posting
    returns all zeros).
    """
    now = datetime.now(timezone.utc)
    result = []
    for post in load_post_history():
        posted_at = datetime.fromisoformat(post["posted_at"])
        if posted_at.tzinfo is None:
            posted_at = posted_at.replace(tzinfo=timezone.utc)
        age_hours = (now - posted_at).total_seconds() / 3600
        if age_hours >= hours:
            result.append(post)
    return result
