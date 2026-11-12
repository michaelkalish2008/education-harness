"""Install self-check: runs every core tool against a throwaway workspace."""

from __future__ import annotations

import tempfile
from pathlib import Path

import yaml

from .core import HarnessError, Workspace


def run() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "learning"
        ws = Workspace(root)
        checks: list[tuple[str, bool]] = []

        def ok(name: str, cond: bool) -> None:
            checks.append((name, bool(cond)))

        ws.init_project("check", question="Does the harness work?")
        plan_path = root / "projects/check/program.yaml"
        plan = yaml.safe_load(plan_path.read_text())
        plan["steps"] = [{"id": "s1", "does": "try it", "concepts": ["checking"]}]
        plan_path.write_text(yaml.safe_dump(plan))
        ok("workspace created", (root / ".private/learner.yaml").exists() and (root / ".gitignore").exists())
        ws.write_solution("check", "s1", ["look closely"], "42", "count carefully",
                          [{"problem": "try 43"}, {"problem": "try 44"}])
        try:
            ws.record_attempt("check", "s1", "   ")
            ok("blank attempt refused", False)
        except HarnessError:
            ok("blank attempt refused", True)
        ok("hint served", ws.reveal_solution("check", "s1", "hint")["content"] == "look closely")
        r = ws.reveal_solution("check", "s1", "method")
        ok("method comes with a follow-on", "follow_on" in r)
        try:
            ws.set_status("check", "s1", "drafted", "tutor")
            ok("drafted waits for learner work", False)
        except HarnessError:
            ok("drafted waits for learner work", True)
        ws.record_attempt("check", "s1", "my own try")
        ok("drafted after learner work", ws.set_status("check", "s1", "drafted", "tutor")["status"] == "drafted")
        try:
            ws.set_status("check", "s1", "defended", "tutor", {"explained": True})
            ok("only the validator defends", False)
        except HarnessError:
            ok("only the validator defends", True)
        ws.post_note("check", "s1", "tutor", "validator", "Explained the method well.")
        ok("notes reach their role", len(ws.get_progress("check", "tutor")["notes"]) == 1)
        d = ws.add_diary_entry("Counting carefully finally clicked.", project="check")
        ok("search finds the diary", any(x["file"] == d["saved"]
                                         for x in ws.search_memory("counting clicked", scope="reflection")["results"]))
        ok("index rebuilds from files", ws.rebuild_index()["indexed"] >= 2)

    width = max(len(n) for n, _ in checks)
    for name, passed in checks:
        print(f"{'ok  ' if passed else 'FAIL'}  {name.ljust(width)}")
    failed = [n for n, p in checks if not p]
    print("Self-check passed." if not failed else f"Self-check failed: {len(failed)} check(s).")
    return 1 if failed else 0


def run_semantic() -> int:
    """Real-model check: downloads the model once (about 70 MB) and tests a meaning-based search."""
    from .semantic import FastEmbedder, extra_installed, model_cache
    if not extra_installed():
        print('The semantic extra is not installed. Run: .venv/bin/pip install -e ".[semantic]"')
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        ws = Workspace(Path(tmp) / "learning")
        ws.ensure_workspace()
        ws.add_diary_entry("How fast does an automobile drop in worth each year?", title="car")
        ws.add_diary_entry("Neighborhood canopy and summer temperature looked related.", title="trees")
        ws.add_diary_entry("Softmax turns scores into probabilities.", title="softmax")
        print("Loading the model (first run downloads it)...")
        r = ws.index.enable_semantic(FastEmbedder(model_cache()))
        hits = ws.search_memory("vehicle depreciation", scope="reflection")["results"]
        ok = bool(hits) and "car" in hits[0]["file"]
        print(f"indexed {r['reembedded']} records; top hit for 'vehicle depreciation': "
              f"{hits[0]['file'] if hits else 'none'}")
        print("Semantic check passed." if ok else "Semantic check FAILED.")
        return 0 if ok else 1
