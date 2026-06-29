"""
Agentic learner — reads metrics, finds patterns, rewrites learnings.md.

This is the heart of the self-learning loop. Raw numbers (42 likes, 3 retweets)
are meaningless on their own. The agent's job is to find WHY certain posts
outperformed others and distill that into actionable rules for the poster agent.

A deterministic script could sort posts by likes — but it couldn't reason about
WHY the top post worked. Was it the question format? The topic? The brevity?
That interpretation requires judgment. That's why this is agentic.

Flow:
  1. Load full post history with metrics from post_history.json
  2. Read current learnings.md (so we build on existing knowledge, not restart)
  3. Ask Claude to analyze, synthesize, and rewrite the knowledge base
  4. Overwrite learnings.md with the updated version
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anthropic import Anthropic
from dotenv import load_dotenv
from tools import storage

load_dotenv()


SYSTEM_PROMPT = """You are a data-driven social media strategist.
You analyze post performance to extract repeatable insights.
You write concisely and prioritize evidence — no vague advice like "be authentic".
Every insight you write should be backed by specific data from the posts."""


def _format_post_history(posts: list[dict]) -> str:
    if not posts:
        return "No posts with metrics yet."

    lines = []
    for p in posts:
        m = p.get("metrics", {})
        lines.append(
            f'Post: "{p["text"]}"\n'
            f'  Posted at : {p.get("posted_at", "unknown")}\n'
            f'  Likes     : {m.get("likes", 0)}\n'
            f'  Retweets  : {m.get("retweets", 0)}\n'
            f'  Replies   : {m.get("replies", 0)}\n'
            f'  Impressions: {m.get("impressions", 0)}\n'
        )

    return "\n".join(lines) if lines else "No posts with fetched metrics yet."


def analyze_and_learn() -> str:
    """
    Analyze post history, update learnings.md with fresh insights.
    Returns the new learnings content.
    """
    posts = storage.load_post_history()
    current_learnings = storage.read_learnings()
    history_text = _format_post_history(posts)

    if history_text == "No posts with fetched metrics yet.":
        print("No metric data available yet. Run metrics_collector.py first.")
        return current_learnings

    user_message = f"""Here is the current knowledge base built from previous analyses:

{current_learnings if current_learnings.strip() and "No data yet" not in current_learnings else "Empty — this is the first analysis."}

---

Here is the full post history with engagement metrics:

{history_text}

---

Analyze the data and produce an updated knowledge base in markdown.

Structure it with these sections:
## What Works
Specific patterns that correlate with higher engagement. Back each point with data.

## What to Avoid
Patterns that correlate with low engagement. Back each point with data.

## Best Topics
Topics or themes that have resonated most.

## Style Notes
Tone, format, length, structure observations from high-performing posts.

## Open Questions
Things we don't have enough data to conclude yet — what to test next.

Rules:
- Be specific and data-backed. "Questions outperform statements (avg 3.2x more likes)" not "ask questions".
- Consolidate: don't repeat insights already in the current knowledge base unless new data strengthens them.
- Remove insights that new data has disproved.
- Keep it concise — this file is read before every post, so clarity matters."""

    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    new_learnings = response.content[0].text.strip()
    storage.write_learnings(new_learnings)

    print("Learnings updated.")
    print("---")
    print(new_learnings)

    return new_learnings


if __name__ == "__main__":
    analyze_and_learn()
