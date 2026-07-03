"""
One Claude agent.

Loads its system prompt from .claude/agents/x_posting_agent.md so the
definition lives in one place. Uses an agentic tool-use loop: Claude
decides which tools to call and when, rather than hardcoded function
calls pretending to be intelligence.

Available tools:
  bash           — run scripts in scripts/ or read data files
  write_learnings — overwrite learnings.md with updated content

Usage:
  python agent.py "POST: write and publish one tweet"
  python agent.py "LEARN: analyze metrics and update learnings.md"
"""

import os
import subprocess
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent
AGENT_DEF = ROOT / ".claude" / "agents" / "x_posting_agent.md"

TOOLS = [
    {
        "name": "bash",
        "description": (
            "Run a shell command. Allowed: reading data files with 'cat', "
            "running scripts with 'python scripts/<name>.py [args]'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to run"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "write_learnings",
        "description": "Overwrite learnings.md with updated insight content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Full markdown content for learnings.md"},
            },
            "required": ["content"],
        },
    },
]

# Only allow reading data files and calling scripts — nothing destructive.
_ALLOWED_PREFIXES = ("cat ", "python scripts/", "python3 scripts/")


def _run_bash(command: str) -> str:
    if not any(command.strip().startswith(p) for p in _ALLOWED_PREFIXES):
        return f"Error: not allowed. Permitted prefixes: {_ALLOWED_PREFIXES}"
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, cwd=str(ROOT), timeout=30
        )
        output = result.stdout
        if result.stderr:
            output += f"\nstderr: {result.stderr}"
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 30s"
    except Exception as e:
        return f"Error: {e}"


def _write_learnings(content: str) -> str:
    path = ROOT / "learnings.md"
    # Respect DATA_DIR if set (Render persistent disk)
    data_dir = os.getenv("DATA_DIR")
    if data_dir:
        path = Path(data_dir) / "learnings.md"
    path.write_text(content, encoding="utf-8")
    return f"learnings.md updated ({len(content)} chars)"


def _load_system_prompt() -> str:
    """Load system prompt from the agent definition, stripping YAML frontmatter."""
    text = AGENT_DEF.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.index("---", 3)
        text = text[end + 3:].strip()
    return text


def run(task: str) -> None:
    system = _load_system_prompt()
    client = Anthropic()
    messages = [{"role": "user", "content": task}]

    print(f"[agent] {task}\n")

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        for block in response.content:
            if hasattr(block, "text") and block.text:
                print(f"[agent] {block.text}")

        if response.stop_reason != "tool_use":
            break

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            if block.name == "bash":
                cmd = block.input["command"]
                print(f"[tool]  $ {cmd}")
                output = _run_bash(cmd)
                print(f"[tool]  {output[:300]}")
            elif block.name == "write_learnings":
                print("[tool]  write_learnings")
                output = _write_learnings(block.input["content"])
                print(f"[tool]  {output}")
            else:
                output = f"Error: unknown tool '{block.name}'"

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": output,
            })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent.py <task>")
        print('  e.g. python agent.py "POST: write and publish one tweet"')
        sys.exit(1)
    run(" ".join(sys.argv[1:]))
