---
name: update-plugin
description: Maintainer release path for this repo. Use when someone says "update plugin", "release the plugin", "ship/save the plugin" or "bump the version": test, bump the version everywhere, build the .plugin, commit on a branch, push, open or update the pull request, and present the install card.
---

# Update plugin

For whoever maintains this repo or a fork of it. Run every step in order without stopping unless one fails, then report in a few lines: version, tests, commit, PR link, install card. Never merge, never push to the default branch.

Read identity from git, never hardcode it:
```bash
REMOTE=$(git remote | head -1); URL=$(git remote get-url "$REMOTE")
SLUG=$(echo "$URL" | sed -E 's#.*github.com[:/]##; s#\.git$##')       # owner/repo
BASE=$(git remote show "$REMOTE" | sed -n 's/.*HEAD branch: //p')      # default branch
NAME=$(git config user.name || git log -1 --format=%an); EMAIL=$(git config user.email || git log -1 --format=%ae)
```

## 1. Branch
If on `$BASE`, `git switch -c <short-feature-name>`. Mention any uncommitted changes you didn't make; they ship too.

## 2. Test
```bash
cd mcp && UV_PROJECT_ENVIRONMENT=$HOME/.cache/eh-venv uv run --extra test pytest -q
```
A `mcp/.venv` built on another OS won't run; a separate `UV_PROJECT_ENVIRONMENT` avoids it. Fix failures first.

## 3. Bump the version (minor unless told otherwise)
`grep -rn '"X.Y.Z"' --include=*.json --include=*.py .` and change every hit together: `plugin.json`, `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `mcp/src/eh_mcp/server.py`, `mcp/tests/test_plugin_package.py`. Put the new version first on the README `## Status` line with one sentence on what changed. Re-run tests; the build refuses mismatched manifests.

## 4. Build
`bash scripts/build-plugin.sh` writes `dist/education-harness.plugin` (git-ignored). If the folder can't delete files, build to a path outside the repo and copy it over `dist/`.

## 5. Commit
`git add -A && git -c user.name="$NAME" -c user.email="$EMAIL" commit` with a summary line and short bullets, plus any attribution lines your host requires.

## 6. Push
`git push -u "$REMOTE" <branch>`. If the environment refuses pushes (a sandbox that allows only clone and fetch), push from another checkout: bundle the new commits (`git bundle create /tmp/rel.bundle <last-pushed-commit>..HEAD`), carry the bundle to a checkout that can push, `git fetch /tmp/rel.bundle HEAD`, `git branch -f <branch> FETCH_HEAD`, `git push origin <branch>:<branch>`. Don't move that checkout's default branch. Remove bundles afterwards. Don't retry a refused push the same way.

## 7. Pull request
`gh pr create --base "$BASE" --head <branch>`; if GraphQL is blocked, use REST: `gh api repos/$SLUG/pulls -f base="$BASE" -f head=<branch> -f title=... -F body=@body.md --jq .html_url`. Body: what changes, how it was verified (tests, built package, any end-to-end check), what wasn't exercised. If a PR is already open for the branch, the push updated it; confirm its head sha.

## 8. Present the install card
Check `unzip -p dist/education-harness.plugin .claude-plugin/plugin.json` shows the new version. In the Claude app, send the file with the file-sending tool so its install card appears (copy it to a temp path first if the host requires); elsewhere, give its path. Don't just say "reinstall".
