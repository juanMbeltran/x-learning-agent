"""
One Claude agent.

Loads its system prompt from .claude/agents/x_posting_agent.md so the
definition lives in one place. Runs an agentic tool-use loop: Claude
decides which tools to call and when.

Available tools:
  bash — read data files, check the time, run scripts in scripts/

Usage:
  python agent.py "Check what needs to be done right now and do it."
"""

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
            "Run a shell command. Allowed: 'date' to check current time, "
            "'cat' to read data files, 'python scripts/<name>.py [args]' to run scripts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to run"},
            },
            "required": ["command"],
        },
    },
]

_ALLOWED_PREFIXES = ("date", "cat ", "python scripts/", "python3 scripts/")

MAX_TOOL_ITERATIONS = 3


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

    print(f"[agent] {task}\n", flush=True)

    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        for block in response.content:
            if hasattr(block, "text") and block.text:
                print(f"[agent] {block.text}", flush=True)

        if response.stop_reason != "tool_use":
            return

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            cmd = block.input["command"]
            print(f"[tool]  $ {cmd}", flush=True)
            output = _run_bash(cmd)
            print(f"[tool]  {output[:300]}", flush=True)

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": output,
            })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    print(f"[agent] Stopped after {MAX_TOOL_ITERATIONS} tool calls without finishing.", flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent.py <task>")
        sys.exit(1)
    run(" ".join(sys.argv[1:]))
