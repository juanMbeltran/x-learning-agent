#!/usr/bin/env python3
"""
Deterministic script: overwrite learnings.md with content from stdin.

Usage:
  echo "content" | python scripts/write_learnings.py
  python scripts/write_learnings.py << 'EOF'
  ## What Works
  ...
  EOF
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from tools import storage

load_dotenv()


def main() -> None:
    content = sys.stdin.read()
    if not content.strip():
        print("Error: no content provided on stdin.", file=sys.stderr)
        sys.exit(1)
    storage.write_learnings(content)
    print(f"learnings.md updated ({len(content)} chars)")


if __name__ == "__main__":
    main()
