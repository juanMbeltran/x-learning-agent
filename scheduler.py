"""
Deterministic scheduler — the conductor of the whole system.

This file decides WHEN things run. It never makes content decisions.
It just wakes up the right function at the right time.

Daily schedule:
  09:00  — post a tweet
  13:00  — post a tweet
  18:00  — post a tweet
  Every 6h — collect metrics for recent posts
  20:00  — run the learner agent (after the day's metrics are in)

Why not let the agent decide when to post?
Because timing should be consistent and predictable, not creative.
An agent scheduling its own runs is a recipe for chaos.
"""

import time
import logging
import schedule
from dotenv import load_dotenv

from agents.poster_agent import generate_and_post
from agents.learner_agent import analyze_and_learn
from metrics_collector import collect_all_metrics

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def run_poster():
    log.info("--- Poster agent starting ---")
    try:
        result = generate_and_post()
        log.info(f"Posted: {result['post_id']} — {result['text'][:60]}...")
    except Exception as e:
        log.error(f"Poster agent failed: {e}")


def run_metrics():
    log.info("--- Metrics collector starting ---")
    try:
        collect_all_metrics()
    except Exception as e:
        log.error(f"Metrics collector failed: {e}")


def run_learner():
    log.info("--- Learner agent starting ---")
    try:
        analyze_and_learn()
        log.info("Learnings updated.")
    except Exception as e:
        log.error(f"Learner agent failed: {e}")


# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------

schedule.every().day.at("09:00").do(run_poster)
schedule.every().day.at("13:00").do(run_poster)
schedule.every().day.at("18:00").do(run_poster)

schedule.every(6).hours.do(run_metrics)

schedule.every().day.at("20:00").do(run_learner)


if __name__ == "__main__":
    log.info("Scheduler started. Waiting for jobs...")
    log.info("Jobs registered:")
    for job in schedule.jobs:
        log.info(f"  {job}")

    while True:
        schedule.run_pending()
        time.sleep(30)
