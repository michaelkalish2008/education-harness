import json
import subprocess
import sys
from pathlib import Path

import pytest

GUARD = Path(__file__).with_name("guard.py")


def run(tool, **ti):
    p = subprocess.run([sys.executable, str(GUARD)], input=json.dumps({"tool_name": tool, "tool_input": ti}),
                       capture_output=True, text=True)
    return p.returncode


@pytest.mark.parametrize("tool,ti,code", [
    ("Read", {"file_path": "/u/learning/projects/trees/solutions/s1.yaml"}, 2),
    ("Read", {"file_path": "/u/learning/projects/trees/program.yaml"}, 0),
    ("Read", {"file_path": "/u/learning/.private/learner.yaml"}, 0),
    ("Grep", {"pattern": "slope", "path": "projects/trees/solutions"}, 2),
    ("Edit", {"file_path": "/u/learning/projects/trees/progress.yaml"}, 2),
    ("Write", {"file_path": "/u/learning/.private/diary/x.md"}, 2),
    ("Write", {"file_path": "/u/learning/projects/trees/work/fit.py"}, 0),
    ("Bash", {"command": "cat projects/trees/solutions/s1.yaml"}, 2),
    ("Bash", {"command": "echo hi > .private/log/x.md"}, 2),
    ("Bash", {"command": "cat .private/learner.yaml"}, 0),
    ("Bash", {"command": "python work/fit.py"}, 0),
    ("Bash", {"command": "sed -i s/x/y/ projects/trees/progress.yaml"}, 2),
])
def test_guard(tool, ti, code):
    assert run(tool, **ti) == code


def test_malformed_event_never_blocks():
    p = subprocess.run([sys.executable, str(GUARD)], input="not json", capture_output=True, text=True)
    assert p.returncode == 0
