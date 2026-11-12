#!/usr/bin/env python3
"""Best-effort guard (Claude Code PreToolUse hook).

Keeps the agent's access to protected files going through the harness tools:
- no direct reads of a project's solutions/ (reveals go through reveal_solution,
  which logs what was seen and pairs it with a follow-on problem);
- no direct edits to progress.yaml, solutions/ or .private/.

A determined learner can still open these files themselves; that is their choice.
Exit code 2 blocks the tool call and shows the message to the agent.
"""

from __future__ import annotations

import json
import re
import sys

SOLUTIONS = re.compile(r"(^|[/\\])solutions([/\\]|$)")
PROTECTED_EDIT = re.compile(r"(^|[/\\])(solutions([/\\]|$)|\.private([/\\]|$)|progress\.yaml$)")
BASH_WRITE = re.compile(r"(>|\btee\b|\bsed\s+-i|\brm\b|\bmv\b|\bcp\b|\btouch\b|\btruncate\b|\bchmod\b|"
                        r"\bperl\s+-[a-z]*i|open\([^)]*['\"][wa])")
BASH_PROTECTED = re.compile(r"(\.private[/\\ '\"]|\.private$|progress\.yaml)")

READ_TOOLS = {"Read", "Grep", "Glob", "NotebookRead", "LS"}
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def paths_in(tool_input: dict) -> list[str]:
    keys = ("file_path", "path", "notebook_path", "pattern", "glob")
    return [str(tool_input[k]) for k in keys if tool_input.get(k)]


def block(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(2)


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # never break the session on a malformed event
    tool = event.get("tool_name", "")
    ti = event.get("tool_input", {}) or {}

    if tool in READ_TOOLS and any(SOLUTIONS.search(p) for p in paths_in(ti)):
        block("Solutions are shown through reveal_solution, so what the learner sees is logged "
              "and paired with a follow-on problem. Use that tool.")
    if tool in EDIT_TOOLS and any(PROTECTED_EDIT.search(p) for p in paths_in(ti)):
        block("progress.yaml, solutions/ and .private/ change only through the harness tools "
              "(set_status, write_solution, record_attempt, post_note and the rest).")
    if tool == "Bash":
        cmd = str(ti.get("command", ""))
        if SOLUTIONS.search(cmd):
            block("Solutions are shown through reveal_solution, not the shell.")
        if BASH_PROTECTED.search(cmd) and BASH_WRITE.search(cmd):
            block("Changes to progress.yaml and .private/ go through the harness tools, not the shell.")
    sys.exit(0)


if __name__ == "__main__":
    main()
