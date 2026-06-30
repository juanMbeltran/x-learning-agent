# Self-Learning X Posting Agent

An autonomous agent that posts on X (Twitter) several times a day, reads its own engagement metrics, learns what works, and uses those learnings to write better posts the next day.

Built as a learning project to understand the difference between deterministic code and agentic AI, and how to combine both in a real system.

---

## How It Works

```
Post to X → Wait for engagement → Read metrics → Learn what worked
    ↑                                                      |
    └──────────── Post better tomorrow ◄───────────────────┘
```

Every day the agent:
1. Posts 3 tweets (9am, 1pm, 6pm UTC) written by Claude based on past learnings
2. Collects engagement metrics every 6 hours
3. At 8pm UTC runs a learner agent that reads all metrics and rewrites `learnings.md` with updated insights

---

## Project Structure

```
├── scheduler.py           — runs all jobs on a timer (deterministic)
├── metrics_collector.py   — fetches engagement metrics from X (deterministic)
├── agents/
│   ├── poster_agent.py    — Claude writes and posts tweets (agentic)
│   └── learner_agent.py   — Claude reads metrics and updates learnings (agentic)
├── tools/
│   ├── x_client.py        — Zernio API wrapper (deterministic)
│   ├── storage.py         — reads/writes local files (deterministic)
│   └── get_account_id.py  — one-time setup utility
├── learnings.md           — the agent's evolving knowledge base
├── post_history.json      — log of all posts and their metrics
└── PLAN.md                — full architecture and design decisions
```

---

## Key Concept: Deterministic vs Agentic

Not every task needs AI. This project deliberately mixes both:

| Task | Approach | Why |
|---|---|---|
| Scheduling posts | Deterministic | Time-based logic, no judgment needed |
| Writing a tweet | Agentic | Needs creativity and context |
| Fetching metrics | Deterministic | Same API call every time |
| Interpreting metrics | Agentic | Requires reasoning about why things worked |
| Reading/writing files | Deterministic | Pure I/O |

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/x-learning-agent.git
cd x-learning-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create your `.env` file

```bash
cp .env.example .env
```

Fill in the values:

```
ANTHROPIC_API_KEY=your_key_from_console.anthropic.com
ZERNIO_API_KEY=your_key_from_zernio.com
ZERNIO_ACCOUNT_ID=your_twitter_account_id_in_zernio
DATA_DIR=/data  # only needed on Render, omit locally
```

### 4. Find your Zernio account ID

Connect your X account to Zernio first, then run:

```bash
python tools/get_account_id.py
```

Copy the printed ID into `.env` as `ZERNIO_ACCOUNT_ID`.

### 5. Run locally

```bash
python scheduler.py
```

---

## Deploy to Render.com

1. Push the repo to GitHub
2. Create a **Background Worker** on Render
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python scheduler.py`
5. Add environment variables via the Environment tab
6. Add a **Persistent Disk** (mount path: `/data`) — required so learnings survive redeploys
7. Deploy

---

## Services Used

- **[Anthropic Claude](https://console.anthropic.com)** — AI model for writing tweets and analyzing metrics
- **[Zernio](https://zernio.com)** — API that connects to X (Twitter)
- **[Render.com](https://render.com)** — cloud hosting for 24/7 operation

---

## Estimated Cost (7-day run)

| Service | Cost |
|---|---|
| Anthropic API | ~$0.10 |
| Zernio API | ~$1–2 |
| Render persistent disk | ~$0.06 |
| **Total** | **~$2** |
