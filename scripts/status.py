#!/usr/bin/env python3
"""
Print a clean status summary for the agent to reason about.

Output example:
  current_utc_hour: 13
  hours_since_last_post: 4.2
  hours_since_last_metrics_fetch: 2.1
  learnings_updated_today: false
"""
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from tools import storage

load_dotenv()


def main() -> None:
    now = datetime.now(timezone.utc)

    # Hours since last post
    posts = storage.load_post_history()
    if posts:
        last_post = datetime.fromisoformat(posts[0]["posted_at"])
        if last_post.tzinfo is None:
            last_post = last_post.replace(tzinfo=timezone.utc)
        hours_since_post = (now - last_post).total_seconds() / 3600
    else:
        hours_since_post = 9999

    # Hours since last metrics fetch
    last_fetch = None
    for post in posts:
        fetched = post.get("metrics", {}).get("last_fetched")
        if fetched:
            t = datetime.fromisoformat(fetched)
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            if last_fetch is None or t > last_fetch:
                last_fetch = t
    hours_since_fetch = (now - last_fetch).total_seconds() / 3600 if last_fetch else 9999

    # Was learnings.md updated today?
    data_dir = Path(os.getenv("DATA_DIR", Path(__file__).parent.parent))
    learnings_path = data_dir / "learnings.md"
    if learnings_path.exists():
        mtime = datetime.fromtimestamp(learnings_path.stat().st_mtime, tz=timezone.utc)
        updated_today = mtime.date() == now.date()
    else:
        updated_today = False

    # Posts made today (UTC)
    posts_today = sum(
        1 for p in posts
        if datetime.fromisoformat(p["posted_at"]).replace(tzinfo=timezone.utc).date() == now.date()
    )

    print(f"current_utc_hour: {now.hour}")
    print(f"hours_since_last_post: {hours_since_post:.1f}")
    print(f"posts_today: {posts_today}")
    print(f"hours_since_last_metrics_fetch: {hours_since_fetch:.1f}")
    print(f"learnings_updated_today: {str(updated_today).lower()}")


if __name__ == "__main__":
    main()
