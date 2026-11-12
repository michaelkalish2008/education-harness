#!/usr/bin/env bash
# Starts the education harness MCP server bundled in this plugin.
# 1. uv runs the bundled server (it fetches a suitable Python itself; first run takes a minute).
# 2. EH_DEV=1 runs a maintainer's repo venv instead ($EH_REPO/mcp/.venv), for development.
# 3. Without uv, a repo venv is used if one exists; otherwise the server can't start.
# The app may start servers with a minimal PATH, so common install locations are added.
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-$HOME/.cache/education-harness/venv}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEV="${EH_REPO:-$HOME/Documents/education-harness}/mcp/.venv/bin/eh-mcp"

if [ "${EH_DEV:-}" = "1" ] && [ -x "$DEV" ]; then
  exec "$DEV"
fi
if command -v uv >/dev/null 2>&1; then
  exec uv run --quiet --frozen --project "$HERE/mcp" eh-mcp
fi
if [ -x "$DEV" ]; then
  exec "$DEV"
fi
echo "education-harness: uv is not installed. Install it once (https://docs.astral.sh/uv/) and restart the Claude app." >&2
exit 1
