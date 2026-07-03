"""
Deterministic scheduler — decides WHEN things run.

This file has no AI. It just wakes up the agent at the right times.
The agent decides what to do; the scheduler decides when.

Daily schedule (UTC):
  09:00, 13:00, 18:00  — post a tweet
  every 6 hours         — collect engagement metrics
  20:00                 — analyze metrics and update learnings.md
"""

import logging
import subprocess
import time

import schedule
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def run_poster() -> None:
    log.info("--- Poster starting ---")
    try:
        from agent import run
        run("POST: write and publish one tweet based on past learnings.")
    except Exception as e:
        log.error(f"Poster failed: {e}")


def run_metrics() -> None:
    log.info("--- Metrics collector starting ---")
    try:
        result = subprocess.run(
            ["python", "scripts/collect_metrics.py"],
            capture_output=False,
            text=True,
        )
        if result.returncode != 0:
            log.error("Metrics collector exited with non-zero status")
    except Exception as e:
        log.error(f"Metrics collector failed: {e}")


def run_learner() -> None:
    log.info("--- Learner starting ---")
    try:
        from agent import run
        run("LEARN: read post_history.json, analyze engagement patterns, and update learnings.md.")
    except Exception as e:
        log.error(f"Learner failed: {e}")


schedule.every().day.at("09:00").do(run_poster)
schedule.every().day.at("13:00").do(run_poster)
schedule.every().day.at("18:00").do(run_poster)

schedule.every(6).hours.do(run_metrics)

schedule.every().day.at("20:00").do(run_learner)


if __name__ == "__main__":
    log.info("Scheduler started. Jobs:")
    for job in schedule.jobs:
        log.info(f"  {job}")

    while True:
        schedule.run_pending()
        time.sleep(30)
