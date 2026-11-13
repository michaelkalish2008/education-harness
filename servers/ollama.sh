#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

if ! command -v ollama >/dev/null 2>&1; then
  echo "education-harness: Ollama is not installed (https://ollama.com/download)." >&2
  exit 1
fi
if ! command -v uv >/dev/null 2>&1; then
  echo "education-harness: uv is required (https://docs.astral.sh/uv/)." >&2
  exit 1
fi

exec uv run --quiet --project "$HERE/mcp" eh-ollama "$@"
