"""
Agentic poster — decides WHAT to tweet.

This is where the AI earns its place. A deterministic script could pick
a random template, but it couldn't:
  - Read past learnings and apply them creatively
  - Avoid repeating recent topics or phrasing
  - Adapt tone based on what has worked before

Flow:
  1. Read learnings.md (what has worked / what to avoid)
  2. Read recent posts (to avoid repetition)
  3. Ask Claude to write one tweet
  4. Post it via Zernio
  5. Log it to post_history.json
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anthropic import Anthropic
from dotenv import load_dotenv
from tools import x_client, storage

load_dotenv()


SYSTEM_PROMPT = """You are a sharp, engaging social media writer.
Your goal is to write tweets that spark genuine curiosity or conversation.
You write in a clear, human voice — no hype, no emojis unless they add meaning,
no hollow motivational filler. You adapt based on what has worked before."""


def _format_recent_posts(posts: list[dict]) -> str:
    if not posts:
        return "None yet."
    lines = []
    for p in posts:
        metrics = p.get("metrics", {})
        lines.append(
            f'- "{p["text"]}" '
            f'(likes: {metrics.get("likes", 0)}, '
            f'retweets: {metrics.get("retweets", 0)}, '
            f'impressions: {metrics.get("impressions", 0)})'
        )
    return "\n".join(lines)


def generate_and_post() -> dict:
    """
    Generate a tweet using Claude, post it to X, log it locally.
    Returns the logged post dict.
    """
    learnings = storage.read_learnings()
    recent_posts = storage.get_recent_posts(count=10)

    user_message = f"""Here are your learnings from analyzing past post performance:

{learnings if learnings.strip() else "No learnings yet — this is one of your first posts. Write something genuine and interesting."}

---

Here are your 10 most recent posts (avoid repeating these topics or phrasing):

{_format_recent_posts(recent_posts)}

---

Write ONE tweet that maximizes engagement based on the learnings above.
Rules:
- Under 280 characters
- No hashtags (they look spammy)
- No URLs
- Return only the tweet text — no quotes, no explanation"""

    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    tweet_text = response.content[0].text.strip().strip('"').strip("'")

    print(f"Generated tweet ({len(tweet_text)} chars):\n  {tweet_text}")

    result = x_client.post_tweet(tweet_text)
    storage.log_post(
        post_id=result["post_id"],
        text=result["text"],
        posted_at=result["posted_at"],
    )

    print(f"Posted. ID: {result['post_id']}")
    return result


if __name__ == "__main__":
    generate_and_post()
