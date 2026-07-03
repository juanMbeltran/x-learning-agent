"""
Deterministic scheduler — a heartbeat, nothing more.

This file decides WHEN to wake the agent up. It does not tell the agent
what to do. The agent reads the current state and makes that call itself.

The agent is invoked every 30 minutes. If nothing is due, it does nothing.
"""

import logging
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


def run_agent() -> None:
    log.info("--- Agent waking up ---")
    try:
        from agent import run
        run("Check the current time and post_history.json, then decide what needs to be done right now and do it.")
    except Exception as e:
        log.error(f"Agent failed: {e}")


schedule.every(30).minutes.do(run_agent)


if __name__ == "__main__":
    log.info("Scheduler started. Agent will be invoked every 30 minutes.")
    run_agent()  # run once immediately on startup
    while True:
        schedule.run_pending()
        time.sleep(30)
