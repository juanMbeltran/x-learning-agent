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
├── scheduler.py                 ← DETERMINISTIC: runs jobs on a timer
├── agent.py                     ← THE AGENT: one agentic loop with tools
├── .claude/
│   └── agents/
│       └── x_posting_agent.md  ← agent definition (system prompt + capabilities)
├── scripts/
│   ├── post_tweet.py            ← DETERMINISTIC: post a tweet, log it
│   └── collect_metrics.py      ← DETERMINISTIC: fetch engagement metrics
├── tools/
│   ├── x_client.py             ← DETERMINISTIC: wrapper around Zernio API
│   ├── storage.py              ← DETERMINISTIC: read/write files (respects DATA_DIR)
│   └── get_account_id.py       ← UTILITY: run once at setup
├── /data/
│   ├── learnings.md            ← persistent memory (survives redeploys)
│   └── post_history.json       ← log of all posts + their metrics
├── .env                         ← API keys (never commit this)
└── requirements.txt
```

---

## The Key Design Principle

There is ONE Claude agent (`agent.py`). It loads its system prompt from
`.claude/agents/x_posting_agent.md` and runs an agentic tool-use loop.

The agent reasons and decides. The scripts execute without judgment.

| Component                  | Role                                            |
|----------------------------|-------------------------------------------------|
| `agent.py`                 | The agent — reasoning, deciding, calling tools  |
| `scripts/post_tweet.py`    | Tool — posts a tweet, no decisions              |
| `scripts/collect_metrics.py` | Script — fetches metrics, no decisions        |
| `scheduler.py`             | Timer — decides WHEN, not WHAT or HOW          |
| `tools/x_client.py`        | API wrapper — pure I/O                          |
| `tools/storage.py`         | File I/O — pure I/O                             |

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

## The Agent Tools

`agent.py` exposes two tools to Claude:

**bash** — run safe read operations and scripts:
```
cat learnings.md
cat post_history.json
python scripts/post_tweet.py --text "tweet text here"
python scripts/collect_metrics.py
```

**write_learnings** — overwrite `learnings.md` with updated content.

Claude decides which tools to call and when — this is the agentic part.
The scheduler just triggers it with a task description.

---

## Environment Variables

Required in `.env` locally and in Render's Environment tab:

```
ANTHROPIC_API_KEY=sk-ant-...       # Claude API key from console.anthropic.com
ZERNIO_API_KEY=sk_...              # Zernio API key from their dashboard
ZERNIO_ACCOUNT_ID=...              # Your Twitter account ID in Zernio
DATA_DIR=/data                     # Points to Render's persistent disk (omit locally)
```

---

## tools/x_client.py

Thin wrapper around the Zernio API. Base URL: `https://zernio.com/api/v1`
Auth header: `Authorization: Bearer <ZERNIO_API_KEY>`

**Key lesson learned:** Zernio has three post modes — draft (default), scheduled, and immediate.
Without `"publishNow": True`, posts are silently saved as drafts and never reach X.
A 200 OK response does not mean the intended outcome occurred.

---

## tools/storage.py

All file I/O in one place. Reads `DATA_DIR` from the environment to determine where files live.
Locally defaults to the project root. On Render it points to `/data` (the persistent disk).

---

## Scheduler

```python
schedule.every().day.at("09:00").do(run_poster)
schedule.every().day.at("13:00").do(run_poster)
schedule.every().day.at("18:00").do(run_poster)
schedule.every(6).hours.do(run_metrics)
schedule.every().day.at("20:00").do(run_learner)
```

All times are UTC. Colombia (UTC-5) equivalent: 4am, 8am, 1pm posts / 3pm learner.

---

## The Self-Learning Loop

Day 1:
- `learnings.md` is empty. Agent posts with no prior context.
- Metrics collector runs every 6 hours.
- Evening: agent reads metrics, reasons about patterns, writes first `learnings.md`.

Day 2:
- Agent reads `learnings.md` before each tweet and adapts.
- Evening: agent updates `learnings.md` — synthesizes, doesn't just append.

Day 7+:
- `learnings.md` is a rich, evidence-backed knowledge base.
- Posts are progressively more tailored to what the audience engages with.

---

## Deploy to Render.com

1. Push code to a private GitHub repository.
2. Create a **Background Worker** on Render (no HTTP endpoints needed).
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python scheduler.py`
5. Add environment variables in Render's Environment tab.
6. Add a **Persistent Disk** (mount path: `/data`) — required so learnings survive redeploys.
7. Deploy.

---

## Data Files — Where They Live

| File               | Local (dev)       | Render (prod)  | GitHub         |
|--------------------|-------------------|----------------|----------------|
| learnings.md       | project root      | /data/         | empty snapshot |
| post_history.json  | project root      | /data/         | empty snapshot |
