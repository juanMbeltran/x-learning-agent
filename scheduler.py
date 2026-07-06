"""
Deterministic scheduler — a heartbeat, nothing more.

Wakes the agent every 30 minutes. The agent checks the current state
and decides what action is needed, if any.
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
        run("Check what needs to be done right now and do it.")
    except Exception as e:
        log.error(f"Agent failed: {e}")


schedule.every(30).minutes.do(run_agent)


if __name__ == "__main__":
    log.info("Scheduler started. Agent will be invoked every 30 minutes.")
    run_agent()
    while True:
        schedule.run_pending()
        time.sleep(30)
