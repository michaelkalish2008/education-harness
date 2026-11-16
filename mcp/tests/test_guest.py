"""Guest mode: a separate, short-lived space that never touches the owner's records."""
import json
from datetime import datetime, timedelta, timezone

import asyncio

from test_server import call
from eh_mcp.server import build_server
from eh_mcp import guest as guest_mod


def _owner_with_a_goal(tmp_path):
    s = build_server(tmp_path / "learning")
    asyncio.run(s.call_tool("set_arc", {"goal": "Learn MCMC", "name": "mcmc"}))
    call(s, "note", kind="thought", text="owner's own thought")
    return s


def test_guest_is_a_new_learner_and_leaves_the_owner_untouched(tmp_path):
    s = _owner_with_a_goal(tmp_path)
    owner_before = call(s, "where_am_i")
    assert owner_before["suggested"]["move"] != "welcome"
    started = call(s, "setup", action="guest_start", feature="Sam")
    assert started["guest"] and started["keep"] == "session"
    seen = call(s, "where_am_i")
    assert seen["suggested"]["move"] == "welcome" and seen["arcs"] == [] and seen["guest"]["name"] == "Sam"
    call(s, "note", kind="thought", text="guest thought")
    assert "owner's own thought" not in json.dumps(call(s, "look_back"))
    ended = call(s, "setup", action="guest_end")
    assert ended["deleted"] == started["id"]
    assert not (tmp_path / "learning" / ".private" / "guests" / started["id"]).exists()
    back = call(s, "where_am_i")
    assert "guest" not in back and [a["name"] for a in back["arcs"]] == ["mcmc"]
    assert "guest thought" not in json.dumps(call(s, "look_back"))


def test_kept_guest_survives_end_and_can_resume(tmp_path):
    s = _owner_with_a_goal(tmp_path)
    gid = call(s, "setup", action="guest_start")["id"]
    call(s, "note", kind="thought", text="keep me")
    out = call(s, "setup", action="guest_end", feature="week")
    assert out["kept"]["keep"] == "week"
    assert call(s, "setup", action="guest_status")["kept"][0]["id"] == gid
    assert call(s, "setup", action="guest_resume", feature=gid)["guest"]
    assert "keep me" in json.dumps(call(s, "look_back"))


def test_expired_guests_are_swept_and_a_restart_stays_in_an_active_guest(tmp_path, monkeypatch):
    s = _owner_with_a_goal(tmp_path)
    gid = call(s, "setup", action="guest_start")["id"]
    again = build_server(tmp_path / "learning")                  # server restart mid-session
    assert call(again, "where_am_i")["guest"]["id"] == gid
    later = datetime.now(timezone.utc) + guest_mod.SESSION_IDLE + timedelta(minutes=1)
    monkeypatch.setattr(guest_mod, "_now", lambda: later)
    restarted = build_server(tmp_path / "learning")
    assert "guest" not in call(restarted, "where_am_i")
    assert not (tmp_path / "learning" / ".private" / "guests" / gid).exists()
