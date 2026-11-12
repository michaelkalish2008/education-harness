import json
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[2]


def test_visible_portable_manifest_and_starter_prompts():
    plugin = json.loads((ROOT / "plugin.json").read_text())
    ui = plugin["extensions"]["com.openai"]["interface"]
    assert plugin["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    assert plugin["name"] == "education-harness" and plugin["version"] == "0.7.1"
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
        ("education-harness", "0.7.1")}


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
