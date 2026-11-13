# Core MCP server

Local stdio server over the learner's plain files. The files are the source of truth; the search index is derived from them and can be rebuilt at any time. No keys, no network except `check_links`.

## Install (from this folder, in a venv)

```bash
python3 -m venv .venv                      # Python 3.10 or newer
.venv/bin/pip install -e ".[test]"
.venv/bin/eh-mcp --self-check              # runs every core tool against a throwaway workspace
```

The venv lives at `mcp/.venv` and is git-ignored. The workspace defaults to `~/learning`; set `EH_WORKSPACE` to put it elsewhere.

## Resume with Ollama

From the repository root, after installing Ollama and `uv`:

```bash
ollama pull gpt-oss:20b
./servers/ollama.sh
```

The runner uses Ollama's OpenAI-compatible local endpoint, exposes the same ChatGPT-sized MCP tool surface in-process, and calls `where_am_i` before the first turn. Configuration: `OLLAMA_MODEL`, `OLLAMA_BASE_URL`, `OLLAMA_TIMEOUT`, `OLLAMA_MAX_MESSAGES`, and `EH_WORKSPACE`, or the equivalent command-line flags shown by `./servers/ollama.sh --help`.

## Register with Claude Code (before the plugin is packaged)

```bash
claude mcp add education-harness -- "$PWD/.venv/bin/eh-mcp"
```

Use the absolute path, so Claude Code finds the venv's `eh-mcp` without the venv being activated. The repo's `.mcp.json` (copy it from `mcp.json.example`) points at the same path.

## Tools (26)

| Group | Tools |
| --- | --- |
| Project | `init_project`, `get_plan`, `get_progress`, `write_solution`, `record_attempt`, `reveal_solution`, `record_defense`, `post_note`, `set_status`, `propose_profile_change`, `log_session`, `add_diary_entry`, `check_links` |
| Memory | `search_memory` (keyword always; semantic when on; filters, literal pattern, graph hops), `extract_learnings`, `enable_semantic_search` |
| Library | `add_to_library`, `write_library_summary`, `check_library`, `list_library` |
| Knowledge lifecycle | `record_use`, `sweep_knowledge`, `cluster_library`, `set_knowledge_tier`, `forget_library_item`, `load_standards` |

Refusals come back as `{"refused": "<reason>"}` so the agent can tell the learner plainly.

## Gates the server enforces

- A blank attempt is refused; an explanation so far, a question or a hunch counts.
- `reveal_solution` never refuses. Answer → the method stays to be found (Work backward). Method → a sibling follow-on problem.
- `set_status`: `seen` never blocks; `drafted` needs an attempt, and the follow-on after a reveal; `defended` only with `role="validator"`, the full checklist, and work on a problem the learner hadn't seen solved.
- `write_solution` needs at least two follow-on problems.
- Profile changes apply only when the learner accepts them.
- Notes reach only the role they're addressed to.

The `role` argument is declared by the caller. In Claude Code, subagent tool allowlists and the hook back it up; it is not a security boundary.

## Tests

```bash
.venv/bin/pytest tests ../hooks/test_guard.py
```

## Knowledge organization: small, seasonal, just in time

- **Three scopes, a hard filter on every search:** `meta` (diary, logs, notes, defenses: about the learner), `domain` (library and learnings: what they're learning; the default), `reference` (pinned standards). Metadata filters narrow further before any ranking.
- **Domain tiers:** active (summary, vector, graph), cold (vector dropped, keyword-searchable, rewarmed free), forgotten (a one-line marker, only on the learner's yes).
- **Relevance at each check-in (`sweep_knowledge`):** use fading with a 30-day half-life, plus demand from the plan (concepts of steps not yet defended and their prerequisites), which rewarms cold items just in time. At most 50 active items per area. Items unused for a year and not demanded are proposed for forgetting.
- **Clusters on demand (`cluster_library`):** by shared concept, then by vector similarity; never stored.
- **Standards, pinned:** `eh-mcp --fetch-standards` downloads the Learning Commons Knowledge Graph files once to `~/.cache/education-harness/standards`; `load_standards` pins only openly licensed records (CC BY or CC0), each with its own attribution statement. Pinned standards are never cooled or forgotten. The repo redistributes nothing but codes.

## Library (a knowledge base per area of interest)

The context-layer design from cat, in this package:

- **Summary is the source of truth.** The archivist reads each document and writes a 10–200 word summary in its own words (plus a section map with line or page anchors for long documents). The index holds summaries, never the full text, so long documents are searchable without chunking. Vectors are a disposable cache rebuilt from the summaries.
- **Keyed by content hash, frozen per version.** `check_library` compares each original with its SHA-256: changed files need a new summary, missing files drop out of search. Originals stay where the learner keeps them; records live in `.private/library/`.
- **Two-hop search.** `search_memory` ranks summaries (hop 1) and returns the original's path and section anchors; the agent opens only the 1–3 that match (hop 2).
- **Three ranked lists, fused by reciprocal rank fusion:** semantic over summaries (when on), keyword over summaries, and a literal pattern over the original files that the agent writes from the learner's question. The literal list is decisive only when it matches 40 files or fewer.
- **Metadata filters before ranking:** `area`, `tags`, `concepts`, `type`, `since`, `step`, `project`, and `kinds`.
- **Graph:** documents link to areas and concepts, learnings link to concepts, and concepts link to their prerequisites from the bundled programs. `hops=1` widens a search by one concept step.
- **Deterministic flags:** possible personal information and secrets are detected from the content (rules ported from cat), never taken from a model.

## Smart (semantic) search

Off until the learner turns it on. It covers the learner's records and library summaries alike. `enable_semantic_search("on")` installs the `semantic` extra into this venv, downloads a small local model once (BAAI/bge-small-en-v1.5, about 70 MB, MIT license, via fastembed) and indexes the records, all in the background; keyword search keeps working, and `"status"` reports progress. If anything fails, search stays in keyword mode.

- **Storage:** each 384-dimension vector is compressed with TurboQuant (fixed random rotation, then 4-bit scalar quantization against a codebook computed from the math): 192 bytes instead of 1,536, in the same SQLite file. No vector extension or ANN index.
- **Sync:** every row is keyed by a hash of its text. Writes re-embed only what they touched, in the same transaction; on start, and whenever smart search is turned on, rows whose hash no longer matches are re-embedded. A different model, model file, bit width or seed rebuilds every vector.
- **Results:** keyword and semantic rankings are combined (reciprocal rank fusion).
- **Model check:** the downloaded model files are hashed on first use and the hash is stored; a different hash rebuilds the vectors.

Try it with the real model:

```bash
.venv/bin/pip install -e ".[semantic]"
.venv/bin/eh-mcp --semantic-check
```

## Not in this build yet

The validator-specific read limit in the hook, and the archive and filing tools.
