import pytest
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[2]


def test_visible_portable_manifest_and_starter_prompts():
    plugin = json.loads((ROOT / "plugin.json").read_text())
    ui = plugin["extensions"]["com.openai"]["interface"]
    assert plugin["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    assert plugin["name"] == "education-harness" and plugin["version"] == "0.12.0"
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
        ("education-harness", "0.12.0")}


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


def test_knowledge_map_has_standalone_click_feedback_and_context_exploration():
    page = (ROOT / "skills/start/knowledge-map.html").read_text()
    for marker in ('id="demo"', 'id="exitSample"', 'Back to my map', 'Back to setup',
                   'id="recenter"', 'Map recentered.', 'preventScroll:true',
                   'ResizeObserver', '100dvh', 'tools/call', 'Step 1 of 2', 'Step 2 of 2',
                   'id="buildChip"', 'aria-busy', 'Starting smart search…',
                   'role="progressbar"', 'id="buildElapsed"', 'data-build-stage="indexing"',
                   'attempt<1800', "stopBuild('Check status','Still working')",
                   'id="firstRunNote"', 'The first map takes longer.',
                   'Later updates normally process only new or changed material',
                   'id="tooltip"', 'id="legend"', 'id="inspector"',
                   "requestFullscreen", "row_normalization"):
        if marker == "row_normalization":
            assert marker in (ROOT / "mcp/src/eh_mcp/index.py").read_text()
        else:
            assert marker in page
    assert "semantic vectors" not in page
    assert "See how your learning connects" in page


def test_how_it_works_ships_with_start_and_names_the_real_files():
    text = (ROOT / "skills/start/references/how-it-works.md").read_text()
    assert "references/how-it-works.md" in (ROOT / "skills/start/SKILL.md").read_text()
    for name in ("program.yaml", "progress.yaml", "standards.yaml", "learner.yaml", "MAP.md", "PRINCIPLES.md"):
        assert name in text


def test_maintainer_release_skill_is_in_the_repo_but_not_the_package():
    claude = ROOT / ".claude/skills/update-plugin/SKILL.md"
    codex = ROOT / ".agents/skills/update-plugin/SKILL.md"
    assert claude.read_text() == codex.read_text(), "edit both copies of the update-plugin skill together"
    policy = yaml.safe_load((codex.parent / "agents/openai.yaml").read_text())["policy"]
    assert policy["allow_implicit_invocation"] is False
    build = (ROOT / "scripts/build-plugin.sh").read_text()
    assert '".claude/*"' in build and '".agents/*"' in build


CORE_WORDS = {"start": 900, "tutor": 1400, "plan": 900, "reflect": 950, "review": 600}


@pytest.mark.parametrize("name,limit", sorted(CORE_WORDS.items()))
def test_skill_cores_stay_small_and_their_references_exist(name, limit):
    """Skill bodies load whole; detail lives in references/ and loads only when a pointer says so."""
    import re
    folder = ROOT / "skills" / name
    body = (folder / "SKILL.md").read_text().split("---", 2)[-1]
    assert len(body.split()) <= limit, f"{name} core is {len(body.split())} words; move detail to references/"
    links = re.findall(r"((?:\.\./[\w-]+/)?references/[\w-]+\.md)", body)
    for link in links:
        assert (folder / link).resolve().exists(), f"{name} points to missing {link}"
    pointed = {l.split("/")[-1] for l in links if not l.startswith("..")}
    shipped = {p.name for p in (folder / "references").glob("*.md")} if (folder / "references").exists() else set()
    assert shipped <= pointed, f"{name} has unreferenced files: {sorted(shipped - pointed)}"
