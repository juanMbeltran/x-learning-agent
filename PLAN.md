# Self-Learning X Posting Agent — Architecture Plan

## The Big Picture

Self-learning feedback loop:

```
Post to X → Wait for engagement → Read metrics → Learn what worked → Next post is smarter
    ↑                                                                          |
    └──────────────────────────── Post better tomorrow ◄──────────────────────┘
```

Core insight: not everything should be an agent. A mix of deterministic scripts and agentic
reasoning is what real production systems look like.

---

## Architecture Overview

```
render.com server (/data = persistent disk)
├── scheduler.py          ← DETERMINISTIC: runs jobs on a timer
├── metrics_collector.py  ← DETERMINISTIC: fetches raw X metrics
├── agents/
│   ├── poster_agent.py   ← AGENTIC: Claude decides what/how to post
│   └── learner_agent.py  ← AGENTIC: Claude interprets metrics, writes insights
├── tools/
│   ├── x_client.py       ← DETERMINISTIC: wrapper around Zernio API
│   ├── storage.py        ← DETERMINISTIC: read/write files (respects DATA_DIR)
│   └── get_account_id.py ← UTILITY: run once at setup to find your Zernio account ID
├── /data/
│   ├── learnings.md      ← persistent memory (survives redeploys)
│   └── post_history.json ← log of all posts + their metrics (survives redeploys)
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

## Environment Variables

Required in `.env` locally and in Render's Environment tab on the server:

```
ANTHROPIC_API_KEY=sk-ant-...       # Claude API key from console.anthropic.com
ZERNIO_API_KEY=sk_...              # Zernio API key from their dashboard
ZERNIO_ACCOUNT_ID=...              # Your Twitter account ID in Zernio (run get_account_id.py)
DATA_DIR=/data                     # Points to Render's persistent disk (omit locally)
```

---

## Phase 2 — Deterministic Tools

### tools/x_client.py

Thin wrapper around the Zernio API. Base URL: `https://zernio.com/api/v1`
Auth header: `Authorization: Bearer <ZERNIO_API_KEY>`

```python
def list_accounts() -> list[dict]:
    # GET /v1/accounts — returns all connected social accounts

def post_tweet(text: str) -> dict:
    # POST /v1/posts — publishes immediately to X
    # IMPORTANT: must include "publishNow": True, otherwise Zernio saves as a draft
    # returns { post_id, text, posted_at }

def get_post_metrics(post_id: str) -> dict:
    # GET /v1/analytics?postId={id} — returns likes, retweets, replies, impressions

def get_recent_posts_metrics(limit: int = 20) -> list[dict]:
    # GET /v1/analytics/posts — returns recent posts with their metrics
```

**Key lesson learned:** Zernio has three post modes — draft (default), scheduled, and immediate.
Without `"publishNow": True`, posts are silently saved as drafts and never reach X.
A 200 OK response does not mean the intended outcome occurred — always verify against the real system.

### tools/storage.py

All file I/O in one place. Reads `DATA_DIR` from the environment to determine where files live.
Locally defaults to the project root. On Render it points to `/data` (the persistent disk).

```python
def read_learnings() -> str           # reads learnings.md
def write_learnings(content: str)     # overwrites learnings.md
def log_post(post_id, text, posted_at)        # appends entry to post_history.json
def update_post_metrics(post_id, metrics)     # updates metrics for a post
def load_post_history() -> list[dict]         # returns all posts, newest first
def get_recent_posts(count) -> list[dict]     # returns last N posts
def get_posts_older_than_hours(hours)         # returns posts older than N hours
```

### tools/get_account_id.py

Run this once during setup to find your Twitter account ID in Zernio.
Copy the printed ID into `.env` as `ZERNIO_ACCOUNT_ID`.

```
python tools/get_account_id.py
```

### metrics_collector.py

Loops over post_history.json and fetches metrics for posts aged between 1 and 48 hours.
Under 1 hour: too early, engagement hasn't accumulated.
Over 48 hours: engagement has plateaued, no need to keep polling.

---

## Phase 3 — Agentic Parts

### agents/poster_agent.py

Reads `learnings.md` and the last 10 posts, sends both to Claude as context,
and asks it to write one tweet under 280 characters. Posts it via Zernio and
logs it to `post_history.json`.

### agents/learner_agent.py

Reads the full post history with metrics and the current `learnings.md`.
Asks Claude to find patterns (what topics worked, what styles performed best,
what to avoid) and rewrite `learnings.md` with updated, evidence-backed insights.
Structured in sections: What Works, What to Avoid, Best Topics, Style Notes, Open Questions.

---

## Phase 4 — Scheduler

```python
schedule.every().day.at("09:00").do(run_poster)   # post a tweet
schedule.every().day.at("13:00").do(run_poster)   # post a tweet
schedule.every().day.at("18:00").do(run_poster)   # post a tweet
schedule.every(6).hours.do(run_metrics)            # collect engagement metrics
schedule.every().day.at("20:00").do(run_learner)  # analyze and update learnings.md
```

All times are UTC. Colombia (UTC-5) equivalent: 4am, 8am, 1pm posts / 3pm learner.

---

## Phase 5 — The Self-Learning Loop

Day 1:
- learnings.md is empty. Agent posts with no prior context.
- Metrics collector runs every 6 hours.
- Evening: learner agent reads metrics, writes first insights to learnings.md.

Day 2:
- Poster agent reads learnings.md before each tweet and adapts.
- Evening: learner agent updates learnings.md — synthesizes, doesn't just append.

Day 7+:
- learnings.md is a rich, evidence-backed knowledge base.
- Posts are progressively more tailored to what the audience engages with.

---

## Phase 6 — Deploy to Render.com

1. Push code to a private GitHub repository.
2. Create a **Background Worker** on Render (no HTTP endpoints needed).
3. Connect the GitHub repo — Render auto-deploys on every push.
4. Set environment variables in Render's Environment tab (use "Add from .env").
5. Add a **Persistent Disk** under the Disks tab:
   - Mount path: `/data`
   - Size: 1 GB
   - Without this, learnings.md and post_history.json are wiped on every redeploy.
6. Start command: `python scheduler.py`

**Key lesson learned:** Cloud servers use ephemeral filesystems by default. Any file written
at runtime is deleted when the server redeploys. Data that must survive redeploys needs to
live on a persistent disk (or external database), completely separate from the code.

---

## Data Files — Where They Live

| File               | Local (dev)       | Render (prod)  | GitHub         |
|--------------------|-------------------|----------------|----------------|
| learnings.md       | project root      | /data/         | empty snapshot |
| post_history.json  | project root      | /data/         | empty snapshot |

GitHub only ever receives what you explicitly push. Data files are never pushed automatically.
The live data on Render's disk is the source of truth.

---

## Build Order

1. tools/x_client.py       — connect to Zernio, run get_account_id.py to get ZERNIO_ACCOUNT_ID
2. tools/storage.py        — read/write files
3. agents/poster_agent.py  — get Claude to generate and post a tweet
4. scheduler.py            — wire it together locally
5. metrics_collector.py    — pull real metrics
6. agents/learner_agent.py — the feedback loop closes here
7. Deploy to Render with persistent disk
