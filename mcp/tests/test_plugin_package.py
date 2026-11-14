import json
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[2]


def test_visible_portable_manifest_and_starter_prompts():
    plugin = json.loads((ROOT / "plugin.json").read_text())
    ui = plugin["extensions"]["com.openai"]["interface"]
    assert plugin["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    assert plugin["name"] == "education-harness" and plugin["version"] == "0.10.0"
    assert ui["displayName"] == "Education Harness"
    assert len(ui["shortDescription"]) <= 30
    assert len(ui["defaultPrompt"]) == 3
    assert ui["defaultPrompt"][0].startswith("Let's learn")
    assert any("data-science" in prompt for prompt in ui["defaultPrompt"])


def test_compatibility_manifests_keep_identity_in_sync():
    root = json.loads((ROOT / "plugin.json").read_text())
    codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
    claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    assert {(m["name"], m["version"]) for m in (root, codex, claude)} == {
        ("education-harness", "0.10.0")}


def test_local_mcp_and_start_skill_are_discoverable():
    mcp = json.loads((ROOT / "mcp.json").read_text())
    server = mcp["mcpServers"]["education-harness"]
    assert mcp["$schema"] == "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
    assert server["type"] == "stdio" and server["command"] == "uv"
    assert "${PLUGIN_ROOT}/mcp" in server["args"]
    meta = yaml.safe_load((ROOT / "skills/start/agents/openai.yaml").read_text())
    assert meta["interface"]["display_name"] == "Start learning"
    assert meta["policy"]["allow_implicit_invocation"] is True
    skill = (ROOT / "skills/start/SKILL.md").read_text()
    assert "ordinary language is the interface" in skill.lower()
    assert "teach me <topic>" in skill.lower()
    assert "let's learn" in skill.lower()


def test_claude_app_server_config_and_lockfile():
    # The Claude app starts a plugin's server from .mcp.json; without it the harness tools never appear.
    cfg = json.loads((ROOT / ".mcp.json").read_text())
    server = cfg["mcpServers"]["education-harness"]
    assert server["args"] == ["${CLAUDE_PLUGIN_ROOT}/servers/launch.sh"]
    assert "--frozen" in (ROOT / "servers/launch.sh").read_text()
    assert (ROOT / "mcp/uv.lock").exists()   # --frozen refuses to run without it


def test_catalog_and_academic_advisor_ship_together():
    assert (ROOT / "skills/start/catalog.html").exists()
    advisor = (ROOT / "agents/academic-advisor.md").read_text()
    assert "suggestions are opt-in" in advisor.lower()
    assert "notebooklm" in advisor.lower()
    assert (ROOT / "skills/start/knowledge-map.html").exists()


def test_how_it_works_ships_with_start_and_names_the_real_files():
    text = (ROOT / "skills/start/how-it-works.md").read_text()
    assert "how-it-works.md" in (ROOT / "skills/start/SKILL.md").read_text()
    for name in ("program.yaml", "progress.yaml", "standards.yaml", "learner.yaml", "MAP.md", "PRINCIPLES.md"):
        assert name in text
