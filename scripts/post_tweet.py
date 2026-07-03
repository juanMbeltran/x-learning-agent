#!/usr/bin/env python3
"""
Deterministic script: post a tweet to X.

Takes the tweet text via --text, validates length, posts via Zernio,
and logs the result to post_history.json.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from tools import storage, x_client

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True, help="Tweet text (max 280 chars)")
    args = parser.parse_args()

    text = args.text.strip()
    if len(text) > 280:
        print(f"Error: tweet is {len(text)} chars — exceeds 280 char limit.", file=sys.stderr)
        sys.exit(1)

    result = x_client.post_tweet(text)
    storage.log_post(
        post_id=result["post_id"],
        text=result["text"],
        posted_at=result["posted_at"],
    )
    print(f"Posted: {result['post_id']}")
    print(f"Text:   {result['text']}")


if __name__ == "__main__":
    main()
