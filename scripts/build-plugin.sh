#!/usr/bin/env bash
# Builds education-harness.plugin (a zip the Claude app installs) from this repo.
# Usage: scripts/build-plugin.sh [output-path]   (default: ./dist/education-harness.plugin)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$ROOT/dist/education-harness.plugin}"
cd "$ROOT"

fail() { echo "build-plugin: $*" >&2; exit 1; }
[ -f .claude-plugin/plugin.json ] || fail ".claude-plugin/plugin.json is missing"
[ -f .mcp.json ] || fail ".mcp.json is missing: the Claude app reads it to start the server"
[ -f mcp/uv.lock ] || fail "mcp/uv.lock is missing: servers/launch.sh runs 'uv run --frozen'"
for s in skills/*/; do [ -f "$s/SKILL.md" ] || fail "$s has no SKILL.md"; done
python3 - <<'PY' || fail "manifest versions differ"
import json
v = {json.load(open(p))["version"] for p in ("plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json")}
assert len(v) == 1, v
PY

mkdir -p "$(dirname "$OUT")"
rm -f "$OUT"
zip -qr "$OUT" . \
  -x ".git/*" ".claude/*" ".agents/*" "dist/*" "_to_delete/*" "*/__pycache__/*" "*.pyc" "*/.pytest_cache/*" ".pytest_cache/*" \
     "mcp/.venv/*" "mcp/tests/*" "hooks/*" "docs/*" "templates/*" "scripts/*" "mcp.json.example" "*.DS_Store" ".env"
VERSION="$(python3 -c 'import json;print(json.load(open(".claude-plugin/plugin.json"))["version"])')"
echo "built $OUT (version $VERSION, $(unzip -l "$OUT" | tail -1 | awk '{print $2}') files)"
