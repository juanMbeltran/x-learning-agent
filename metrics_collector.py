"""
Deterministic metrics collector.

Runs on a schedule (see scheduler.py). Loops over post_history.json,
fetches fresh metrics from X for posts that are old enough to have
accumulated engagement, and writes the results back to disk.

There is no AI here. The decision of WHAT to fetch is simple time-based
logic. The actual interpretation of those numbers happens in learner_agent.py.
"""

import sys
from datetime import datetime, timezone
from tools import x_client, storage


# Only fetch metrics for posts between 1 and 48 hours old.
# - Under 1 hour: too early, engagement hasn't had time to accumulate.
# - Over 48 hours: engagement has plateaued; no need to keep polling.
MIN_AGE_HOURS = 1
MAX_AGE_HOURS = 48


def collect_all_metrics() -> None:
    posts = storage.get_posts_older_than_hours(MIN_AGE_HOURS)

    if not posts:
        print("No posts old enough to collect metrics for.")
        return

    collected = 0
    for post in posts:
        post_id = post["post_id"]

        # Skip posts that are too old — engagement has plateaued
        posted_at = datetime.fromisoformat(post["posted_at"])
        if posted_at.tzinfo is None:
            posted_at = posted_at.replace(tzinfo=timezone.utc)
        age_hours = (datetime.now(timezone.utc) - posted_at).total_seconds() / 3600
        if age_hours > MAX_AGE_HOURS:
            continue

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
            print(f"[{post_id}] Failed to fetch metrics: {e}", file=sys.stderr)

    print(f"Done. Updated metrics for {collected} post(s).")


if __name__ == "__main__":
    collect_all_metrics()
