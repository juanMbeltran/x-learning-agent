# Self-Learning X Posting Agent — Architecture Plan

## The Big Picture

Self-learning feedback loop:

```
Post to X → Wait → Read metrics → Learn what worked → Write learnings → Next post is smarter
```

Core insight: not everything should be an agent. A mix of deterministic scripts and agentic
reasoning is what real production systems look like.

---

## Architecture Overview

```
render.com server
├── scheduler.py          ← DETERMINISTIC: runs on a cron timer
├── agents/
│   ├── poster_agent.py   ← AGENTIC: decides what/how to post
│   └── learner_agent.py  ← AGENTIC: interprets metrics, writes insights
├── tools/
│   ├── x_client.py       ← DETERMINISTIC: wrapper around Zernio API
│   └── storage.py        ← DETERMINISTIC: read/write learnings.md and post_history.json
├── metrics_collector.py  ← DETERMINISTIC: fetches raw X metrics
├── learnings.md          ← persistent memory between runs
├── post_history.json     ← log of all posts + their metrics
├── .env                  ← API keys (never commit this)
└── requirements.txt
```

---

## Deterministic vs Agentic — The Core Distinction

| Task                          | Type          | Why                                                  |
|-------------------------------|---------------|------------------------------------------------------|
| Fetch metrics from X API      | Deterministic | Same input → same output. No judgment.               |
| Write a tweet                 | Agentic       | Needs creativity, context, learned patterns          |
| Read/write files              | Deterministic | Pure I/O                                             |
| Interpret engagement patterns | Agentic       | Requires reasoning about causality                   |
| Schedule jobs                 | Deterministic | Time-based logic, no creativity needed               |

Rule of thumb: if you could write an if/else to handle it reliably → deterministic.
If the right answer depends on understanding meaning or context → agentic.

---

## Phase 2 — Deterministic Tools

### tools/x_client.py
Thin wrapper around the Zernio API.

```python
def post_tweet(text: str) -> dict:
    # calls Zernio POST endpoint, returns { tweet_id, timestamp }

def get_tweet_metrics(tweet_id: str) -> dict:
    # returns { likes, retweets, replies, impressions }

def get_recent_posts(count: int = 10) -> list[dict]:
    # returns last N posts you made
```

### tools/storage.py
Reads and writes local files.

```python
def read_learnings() -> str:
    # reads learnings.md, returns as string

def write_learnings(content: str):
    # overwrites learnings.md

def log_post(tweet_id: str, text: str, timestamp: str):
    # appends entry to post_history.json

def update_post_metrics(tweet_id: str, metrics: dict):
    # updates post_history.json entry with latest metrics

def load_post_history() -> list[dict]:
    # returns full post_history.json as a list

def get_recent_posts_local(count: int = 10) -> list[dict]:
    # returns last N posts from post_history.json
```

### metrics_collector.py
Loops over post_history.json, fetches metrics for recent posts, saves them back.

```python
def collect_all_metrics():
    posts = load_post_history()
    for post in posts:
        if post is recent enough (< 48 hours old):
            metrics = x_client.get_tweet_metrics(post["tweet_id"])
            storage.update_post_metrics(post["tweet_id"], metrics)
```

---

## Phase 3 — Agentic Parts

### agents/poster_agent.py
Reads learnings.md and recent posts, then asks Claude to write a tweet.

```python
def generate_post() -> str:
    learnings = storage.read_learnings()
    recent_posts = storage.get_recent_posts_local(10)

    prompt = f"""
    You are a social media expert. Your goal is to write a tweet that maximizes engagement.

    Here are your learnings from past posts:
    {learnings}

    Here are your recent posts (avoid repeating these topics/styles):
    {recent_posts}

    Write ONE tweet (under 280 chars). Return only the tweet text, nothing else.
    """

    # call Claude, return the text
```

### agents/learner_agent.py
Reads post_history.json with metrics, synthesizes patterns, rewrites learnings.md.

```python
def analyze_and_learn():
    posts_with_metrics = storage.load_post_history()
    current_learnings = storage.read_learnings()

    prompt = f"""
    You are an analyst reviewing X (Twitter) post performance.

    Current knowledge base:
    {current_learnings}

    Latest performance data:
    {posts_with_metrics}

    Analyze and update the knowledge base. Look for:
    - What topics got the most likes/retweets?
    - What writing styles perform best (questions, lists, stories)?
    - What times of day correlate with more engagement?
    - What to avoid?

    Return an updated, concise knowledge base in markdown. Consolidate and prioritize
    insights by evidence strength.
    """

    # call Claude, write result to learnings.md
```

---

## Phase 4 — Scheduler

```python
import schedule
import time

# Post 3x per day
schedule.every().day.at("09:00").do(run_poster)
schedule.every().day.at("13:00").do(run_poster)
schedule.every().day.at("18:00").do(run_poster)

# Collect metrics every 6 hours
schedule.every(6).hours.do(collect_metrics)

# Run the learner agent once per day after evening metrics
schedule.every().day.at("20:00").do(run_learner)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## Phase 5 — The Self-Learning Loop

Day 1:
- learnings.md is empty. Agent posts with generic good-faith tweets.
- Metrics collector runs every 6 hours.
- Evening: learner agent reads metrics, writes first insights to learnings.md.

Day 2:
- Poster agent reads learnings.md before each tweet.
- It uses learnings to make better choices.
- Evening: learner agent updates learnings.md — synthesizes, doesn't just append.

Day 7+:
- learnings.md becomes a rich, evidence-backed knowledge base.
- Posts get progressively more tailored.

---

## Phase 6 — Deploy to Render.com

1. Push code to a GitHub repo.
2. Create a Background Worker on Render (no HTTP endpoints needed).
3. Set env vars in Render dashboard: ANTHROPIC_API_KEY, ZERNIO_API_KEY, etc.
4. Start command: python scheduler.py
5. Render keeps it running 24/7.

---

## Build Order

1. tools/x_client.py       — get Zernio working, test posting manually
2. tools/storage.py        — read/write files
3. agents/poster_agent.py  — get Claude to generate a tweet
4. scheduler.py            — wire it together locally
5. metrics_collector.py    — pull real metrics
6. agents/learner_agent.py — the feedback loop closes here
7. Deploy to Render
