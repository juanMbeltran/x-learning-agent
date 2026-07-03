#!/usr/bin/env python3
"""
Deterministic script: fetch engagement metrics for recent posts.

Loops over post_history.json and updates metrics for posts aged
between MIN_AGE_HOURS and MAX_AGE_HOURS. No AI, no judgment — just
the same Zernio API call for every eligible post.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone

from dotenv import load_dotenv
from tools import storage, x_client

load_dotenv()

# Only fetch metrics for posts in this age window.
# Under 1h: engagement hasn't accumulated yet.
# Over 72h: engagement has plateaued.
MIN_AGE_HOURS = 1
MAX_AGE_HOURS = 72


def main() -> None:
    posts = storage.get_posts_older_than_hours(MIN_AGE_HOURS)

    if not posts:
        print("No posts old enough to collect metrics for.")
        return

    collected = 0
    for post in posts:
        posted_at = datetime.fromisoformat(post["posted_at"])
        if posted_at.tzinfo is None:
            posted_at = posted_at.replace(tzinfo=timezone.utc)
        age_hours = (datetime.now(timezone.utc) - posted_at).total_seconds() / 3600
        if age_hours > MAX_AGE_HOURS:
            continue

        post_id = post["post_id"]
        try:
            metrics = x_client.get_post_metrics(post_id)
            storage.update_post_metrics(post_id, metrics)
            print(
                f"[{post_id}] likes={metrics['likes']} "
                f"retweets={metrics['retweets']} "
                f"replies={metrics['replies']} "
                f"impressions={metrics['impressions']}"
            )
            collected += 1
        except Exception as e:
            print(f"[{post_id}] Failed: {e}", file=sys.stderr)

    print(f"Done. Updated metrics for {collected} post(s).")


if __name__ == "__main__":
    main()
