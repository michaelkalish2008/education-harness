# Education Harness — Backward-Design Plugin Outline

Nov 10, 2026 · @Michael Kalish

## Objective

> **This is not an extension of current educational initiatives.** It does not follow school, degree or certification models, and it is not built to align with them. It follows John Dewey's idea of education: people learn by doing real projects, and every project is understood in the context of the society it serves. Standards and frameworks appear only as optional reference points where a project happens to touch them; they never define what is learned.

Ship one plugin that turns a project the learner chooses into a self-run program, and show that adult learners will use it to finish a project they chose and can explain to someone else.

- **Hypothesis:** given the skills alone (no cohort, instructor or credential), an adult learner will build a program from a project they choose, keep working on it for at least 4 weeks, and finish it with something they can show or explain, by their own account.
- **Approach:** work backward from the project. Project → how the solution works → the concepts it depends on → plan. The curriculum is the solution, explained.
- **Delivery:** one plugin built on the shared Agent Skills (SKILL.md) format, tested on Claude Code for v0, with Codex experimental.
- **Not tested yet:** community, minors, a browser version.

## v0 release: circulate fast

The harness is free, with no paid tier. v0 is the smallest thing someone can install in minutes and finish one project with, for adults only. This table is the single definition of v0; every later section is tagged **v0** or **later**, and anything tagged later is not built for this release.

| Item | In v0 | Acceptance test |
| --- | --- | --- |
| Repo | Public, MIT (code) and CC BY 4.0 (content), `PRINCIPLES.md` at the root, tagged releases | A stranger can read the README and know what it is, what it costs, who it is for (adults) and where their conversations go, in 2 minutes |
| Harness | Claude Code is the tested harness. Codex and one local model are listed as experimental: installable, not tested before release | Tested-on matrix in the README |
| Roles and skills | Seven roles, six v0 skills. The learner hears one voice, the tutor, which owns the next step; the mentor joins when the learner zooms out. The lesson planner, validator and archivist are subagents that never talk to the learner (see Roles) | Each skill passes its regression transcripts in Claude Code; the subagents are refused any tool outside their allowlists; the transcripts check which tools the main thread calls |
| Default program | How to be a data scientist: six projects from high-school math to a small transformer, each step mapped to standards. v0 ships the whole path with its standards; every example is built small, from the learner's own interests (see Default program) | Two testers work through the first idea with examples from their own interests, using only the README; one reaches backpropagation |
| Learner-chosen project | The lesson planner builds a plan for a project the learner brings | One tester finishes their own code or data project |
| Install | Claude Code plugin install; `INSTALL.md` registers and checks the core MCP server and asks one question about smart search | Fresh machine to first lesson in under 15 minutes, every command shown first |
| Core MCP server | Required. 16 local tools (see Core MCP server), stdio, no keys; network only for `check_links` and, if chosen, the one-time semantic install; reads and writes the same plain files | Each tool's result matches the files on disk |
| Memory | Diary, notes and learnings with tag filters; keyword search always; semantic search opt-in at install, stored as TurboQuant-compressed vectors in the same SQLite file | A search for a past concept returns the right entry as a snippet, in both modes; after every write, the index matches the files |
| Workspace | One layout under `learning/`, created by `init_project`; filing and archive tools later | A session leaves every harness file in its home |
| Learning loop | Intake (access needs, then preferences); two formats (Solve it, Work backward); an optional short diary; profile changes proposed and confirmed together in one end-of-session prompt | Intake writes `.private/learner.yaml`; no profile change without the learner accepting it |
| Constellation | Six questions per project; readings only when read by hand and link-checked (none bundled in v0) | Every hand-checked link resolves and was read by hand |
| Privacy | `.private/` (profile, proposals, log, diary, attempts, handoffs, learnings, index) git-ignored by default | `git status` after a session shows no private files |

- **Cost to the learner:** the README states plainly that the harness needs a Claude subscription or API access, or a local model with weaker results. Subagents run only when needed (a plan, a defense, a check-in), not every session.
- **Regression transcripts:** each of the six v0 skills ships with 3–5 fixed test conversations, run headless in Claude Code by a script in `tests/`. Pass criteria are about actions, not wording: which tools were called, which files changed, and what was paired (for example, no solution text outside `reveal_solution`, and no reveal without its follow-on problem). About 25 runs per release.

**Core MCP server (v0)**

A thin local server over the learner's plain files, required in v0. It holds no state of its own; the files stay the source of truth. If the server is missing, the tutor says so and stops at every tool-gated step instead of carrying on without it. A tool gate makes a rule hold for the files; the model could still talk around it in chat, which the regression transcripts check.

| Tool | Group | Does | Gates |
| --- | --- | --- | --- |
| `init_project` | Project | Creates the workspace (`learning/`) on first use, then a project folder: copies a default-program project (`program.yaml`, `solutions/`, data) or makes an empty skeleton, plus the `.gitignore` | Nothing else creates those files |
| `get_plan` | Project | Reads `program.yaml` | One shape for state |
| `get_progress` | Project | Reads `progress.yaml` and the open notes addressed to the calling role | One shape for state |
| `write_solution` | Project | Saves a step's hints, worked solution and follow-on problems to `solutions/`; called only by the lesson planner subagent (default-program projects ship them pre-written) | The only way to write `solutions/`; the tutor never sees a solution until it is revealed |
| `record_attempt` | Project | Saves the learner's work on a step to `.private/attempts/` with a timestamp | Principle 1; their explanation so far, a question, a hunch or "let's look at it together" all count; only a blank is refused |
| `reveal_solution` | Project | Serves whatever the learner asks to see: a hint; the answer, after which the method stays to be found (Work backward); or the full method, after which a sibling problem follows with the solution as a worked example | Never refuses. Logs what was seen in `progress.yaml`, so the validator knows, and pairs every reveal with a follow-on problem |
| `record_defense` | Project | Saves a defense in the learner's own words, plus any parked questions, to `.private/handoff/`; the learner reads it and can strike any part before the validator sees it | Only the learner's words, never a paraphrase |
| `post_note` | Project | Leaves a note for one role (tutor, mentor, validator, organizer, lesson planner) in `.private/handoff/`; used for the validator's feedback and for mentor consults | Each role sees only the notes addressed to it |
| `set_status` | Project | Marks a step seen, drafted or defended; defended only by the validator | Principle 4: defended needs the three-part checklist and the learner's own work on a problem they hadn't seen solved; drafted needs an attempt on the follow-on; seen never blocks moving on |
| `propose_profile_change` | Project | Stores intake answers and proposals in `.private/proposals.yaml`; applies those the learner accepts in the end-of-session prompt | No silent profile changes |
| `log_session` | Project | Appends a session note to `.private/log/` | Every session leaves a record |
| `add_diary_entry` | Project | Saves an optional diary entry to `.private/diary/` and indexes it | Never required |
| `check_links` | Project | Fetches each cited link and reports dead ones | Checks, doesn't gate; whether a source supports the claim is checked by hand |
| `search_memory` | Memory | Filters by tags, then ranks by keyword or, when on, similarity; returns snippets with ids | Read-only |
| `extract_learnings` | Memory | Validates and stores a learning record the archivist wrote; the server runs no model | Refuses a record with no link to its source, or with concept tags not found in a `program.yaml` |
| `enable_semantic_search` | Memory | Turns semantic mode on or off; turning it on starts the install and model download in the background and returns at once, with a status check | Search stays in keyword mode until the model is ready |

**Interface decisions (settled for the build)**

- **Workspace root:** everything lives under `learning/` (see Workspace layout). `.private/` sits at the workspace root and is shared by all projects; paths in this outline are relative to `learning/`.
- **Profile proposals:** pending proposals collect in `.private/proposals.yaml` and are offered together in one prompt at session end, along with anything else that needs the learner's yes. The learner accepts, edits or skips each.
- **Work backward answers:** a step in that format carries a non-secret `answer` field in `program.yaml`. The answer is meant to be seen; `solutions/` holds only the method.
- **Handoffs:** roles pass work through `.private/handoff/<project>/<step>/` with `record_defense` and `post_note`; `get_progress` returns the notes addressed to each role.
- **The hook is best-effort.** It blocks the tools and common shell commands that read or edit protected files, but a determined learner can still look, and that is their choice. The gate exists so the agent never hands over a solution unasked, not to police the learner.

* **Runtime:** one Python package with pinned dependencies and one optional `semantic` extra, installed with pipx from the same release tag; stdio transport. `INSTALL.md` starts with a preflight check (Python, pipx, disk space) and explains any fix before running it.
* **Network:** only `check_links`, and, once and only if the learner says yes, the semantic extra's install and the pinned model download.
* **Hook (best-effort):** a Claude Code hook blocks the main thread's direct reads of `solutions/`, including common shell commands (cat, grep, editors), and direct edits to `progress.yaml`, `solutions/` and `.private/`, so access goes through the tools. In validator calls it also limits reads of `.private/` to that step's handoff folder, so the validator never sees the tutoring log.
* **Install:** `INSTALL.md` registers the server through the plugin's `.mcp.json` and runs a self-check. It is pinned to a release tag and the README lists that tag's commit hash, since tags can be moved and an agent will run whatever an install file says. Install only from the main repo.
* **Extras:** optional servers such as GitHub are offered, never installed by default. Every install has a matching uninstall.

**Later, not v0:** diagnose, practice, add-to-portfolio; archive tiers and manifests (`archive_project`, `restore_project`, `sweep_archive`), cold storage and TTL proposals; filing tools (`check_layout`, `move_file`), folder splitting and moves that rewrite references; prerequisite links and graph hops; minors and the guardian mode; pairs and groups; problem formats beyond two; automatic profile updates; per-role outside tools; an optional real-data version of each idea; the job-data pipeline; the 11 concept maps and depth × duration variants; the high-school track; generated constellation readings; non-code projects (product and program management); any community.

## Memory, archive and roles (v0)

The harness keeps a searchable memory of everything the learner has done, so no role reads whole files into context. Raw records stay as written; learnings are extracted from them; one local index covers both. The files are the source of truth: every write tool updates the index in the same step, and the index can be rebuilt from the files at any time.

**Records and learnings**

- **Diary entries** stay exactly as written in `.private/diary/`; they are the evidence.
- **Learnings:** at session end the archivist reads the new diary entries and writes one record per learning: concept, what happened (solved, stuck, the guess and its origin), format, date, tags, and links back to the entry and the project step. `extract_learnings` validates and stores each record; the server itself runs no model. Records are written once and kept; running extraction again proposes additions and never rewrites. Profile proposals and lesson plans read learnings first and open the diary only for context.
- **Tags:** fixed kinds (concept, project, step, format, outcome, standard). Concept tags come from the `concepts` lists in `program.yaml`, so the vocabulary is the plan's own, and `extract_learnings` refuses any other. Prerequisite links between concepts, and graph hops across them, come later; in v0, search filters by tags only.

**Search**

`search_memory` filters by tags first, then ranks what's left, and returns short snippets with ids rather than whole files. Two modes:

| Mode | How it ranks | Setup |
| --- | --- | --- |
| Keyword (always on) | Full-text search (SQLite FTS5) in `.private/index/` | Nothing to install |
| Semantic (opt-in, recommended) | Adds similarity from a small local embedding model; vectors are compressed with TurboQuant and stored as plain rows in the same SQLite file | One question at install; the agent does the rest |

- **Path of least resistance:** `INSTALL.md` asks one plain question: "Turn on smart search? It downloads about 70 MB once and runs only on your computer." On yes, `enable_semantic_search` installs the `semantic` extra and fetches a pinned model, checked by hash, in the background. Keyword search works meanwhile, and the learner never sees model names or settings.
- **Fails safe:** if the install or download fails, search stays in keyword mode and the archivist offers to retry later. The same tool turns the mode on or off at any time.
- **Privacy:** indexing and embedding run locally, and the index lives in `.private/index/`. Anything retrieved into a conversation still goes to the model provider.
- **Maintainer default:** the repo's own config turns semantic search on; for everyone else it is one yes at install.

**Vector storage: TurboQuant**

TurboQuant (Google Research, ICLR 2026) compresses each vector on its own: a fixed random rotation, then scalar quantization against bounds computed from the math rather than learned from the data. With no codebook to train and no ANN index to build, the semantic mode needs no SQLite vector extension, which removes the main install risk on stock macOS Python.

- **Storage:** a 384-dimension embedding takes 1.5 KB as float32 and about 190 bytes at 4 bits, roughly 8× smaller. Tens of thousands of records stay a few megabytes.
- **Search:** a scan over the packed codes, fast at personal scale; no index structure to maintain.
- **Sync:** each row is keyed by record id and a hash of the record's text. Every write tool (`add_diary_entry`, `extract_learnings`, `log_session`, `record_defense`, `post_note`) re-embeds and re-quantizes only the records it touched, in the same transaction as the file write. Because quantization needs no training, one changed record never invalidates the others. On start, the server compares hashes with the files and re-embeds any row that drifted, for example after a hand edit.
- **Fixed settings:** the rotation seed, bit width and model hash are stored in the index; changing any of them rebuilds the whole index.
- **Implementation:** a pinned `turboquant-py`, or a short NumPy implementation of the rotation-and-quantize stage if that package isn't stable enough; decided in build step 1.

**Archive tiers (later)**

| Tier | Holds | Indexed | In v0 |
| --- | --- | --- | --- |
| Active | `projects/` and every record in `.private/` | Full text and embeddings | Yes |
| Pool | `archive/pool/<project-slug>/` with its manifest | Full text and embeddings | Yes |
| Cold | A compressed bundle per project; manifests and learnings stay outside it | Manifests and learnings only | Later |

- **Not in v0.** A finished project simply stays in `projects/`, fully indexed. The archive tools and both tiers below come after the pilot.
- **Records never move:** diary entries, attempts, handoffs and learnings stay in `.private/`, indexed, whatever happens to the project.
- **Two manifests per archived project (later):** `archive/pool/<slug>/manifest.yaml` holds what could be published (summary, concepts, tags, dates, portfolio link); `.private/manifests/<slug>.yaml` holds key learnings, open threads and the last-used date. The archivist drafts both and the learner approves them.
- **Usage state** will live in the private manifest, not in the index, so a rebuild never resets it.
- **Nothing is ever deleted without the learner:** cold storage after 6 months unused and TTL proposals after 12 more will only propose; the learner confirms, and manifests and learnings are always kept.

**Roles**

Seven roles divide the work, but the learner hears one voice. Each role has a fixed set of tools, and any outside tool the learner connects later (storage, calendar, a code host) is granted to one role, not all. Claude Code subagents run one task and return; they can't hold a conversation. So in v0:

- **One voice, one owner of the next step.** The learner talks to the tutor. The tutor always says what comes next, and every other role's work reaches the learner through it.
- **The mentor is a mode, not a second agent.** The learner enters it by asking to zoom out; the tutor offers it at check-in and at the end of a project, and announces the switch in one line. Any role can consult the mentor: main-thread roles directly, subagents through a written note and a written reply.
- **The facilitator and organizer have no voice of their own.** The facilitator runs intake, session start and end and the end-of-session prompt; the organizer's pacing work happens at check-in. Both speak through the tutor.
- **Three subagents work out of sight:** the lesson planner writes plans and solutions, so the tutor never sees a solution before it is revealed; the validator judges from a clean context; the archivist turns diary entries and notes into learnings at check-in.
- **Roles pass work through files** in `.private/handoff/`, never through shared context.

| Role | Runs as | Responsibilities | Skills | Core tools | Built-in tools | Principles |
| --- | --- | --- | --- | --- | --- | --- |
| Tutor | Main thread: the learner's one voice | Works with the learner toward an understanding; shows what they ask to see and carries it into the follow-on; offers other shapes for a problem; tunes into their environment; runs a defense when the learner asks for one, with the validator's questions; relays feedback as next steps; always names the next step; flags struggle to the organizer | tutor | `get_plan`, `get_progress`, `record_attempt`, `reveal_solution`, `record_defense`, `set_status` (seen, drafted), `log_session`, `add_diary_entry`, `search_memory` | Read (the hook blocks `solutions/`); Write and Bash in `work/` | 1, 4, 7, 8 |
| Mentor | Main thread, a mode the learner or any role enters | Keeper of the program's Dewey purpose: ties the work to society and democracy, helps the learner find where the work leads (often one real person who could use it), talks through worries about direction and AI, answers consults from other roles. Gives no step hints and sets no status | mentor | `get_plan`, `get_progress`, `post_note`, `log_session`, `search_memory` | Read | 0, 5, 10, 18 |
| Facilitator | Main thread, speaks through the tutor | Runs intake, session start and end, the end-of-session prompt and the learner controls; routes work to the other roles | check-in | `get_plan`, `get_progress`, `log_session`, `propose_profile_change`, `search_memory` | Read; Write for `commitment.md` | 5, 12, 18 |
| Organizer | Main thread at check-in, speaks through the tutor | Watches trajectory and load: active projects, pace against the learner's own cadence, struggle flags, what the learner says works. Consults the tutor and mentor, proposes changes for the learner to accept, hands accepted changes to the lesson planner | check-in | `get_plan`, `get_progress`, `post_note`, `search_memory` | Read | 2, 5, 13, 18 |
| Lesson planner | Subagent | Turns a project into steps, concepts, solutions and follow-on problems; writes detours and remedial steps; adapts plans the learner accepted; cites standards where they fit | design-from-project | `init_project`, `get_plan`, `write_solution`, `search_memory` | Read; Write for `program.yaml` | 0, 2, 3 |
| Validator | Subagent, clean context; never talks to the learner | Called twice per defense: first to run the code, check links and write open questions with smaller versions; then to read the learner's record and judge the three checks. Consults the mentor by note when a wrong answer shows real growth or a gap looks procedural. Writes feedback for the tutor | validate | `get_progress`, `set_status`, `post_note`, `check_links` | Read for `work/`, `program.yaml` and that step's handoff folder; Bash to run the learner's code | 1, 4, 9 |
| Archivist | Subagent, at check-in | Extracts learnings and tags from diary entries and notes; manages semantic search | archive | `extract_learnings`, `search_memory`, `enable_semantic_search` | Read for `.private/diary/`, `.private/handoff/` and `projects/` | 11, 13 |

Core tools: 13 project and 3 memory, 16 in all; archive and filing tools come later.

**How a defense works (v0)**

A defense is offered, never required. The learner asks for one when they want to explain their work, and a project is complete without it. Nobody stumps, blocks or fails anyone: every defense ends with something to explore and someone to explore it with.

1. **The learner asks for a defense.** The tutor calls the validator.
2. **The validator prepares (first call).** In a clean subagent context holding only the work, the step, the "strong version shows" list and what the learner had already seen, it runs the code, checks links, and writes three or more open questions, including one about a path not taken, each with smaller versions.
3. **The tutor and learner talk it through:** the learner's explanation, the validator's questions offered as invitations, smaller versions when a question doesn't open, parked questions, and one limit of the work. If the learner asks to see an answer, the tutor shows it, as anywhere else, and the record notes it.
4. **The learner reviews the record.** `record_defense` saves their words; they read it and can strike anything before it goes on.
5. **The validator judges (second call).** It reads the work and the record, decides whether the three checks are met, sets the status, and leaves feedback for the tutor: what holds, threads to explore next, formats that might help.
6. **If the validator consults the mentor,** it posts a note; the tutor switches to mentor mode, which reads it with the learner's history and replies by note; a third validator call reads only that reply before it judges.
7. **The tutor relays** what holds and names the next step, as "not yet", never as a fail. Bigger-picture observations wait for the next mentor conversation.

- **Clean context is the validator's guarantee.** It never sees the tutoring, the diary, the profile or the conversation, so its judgment rests on the work and the learner's own words.
- **Always a way back.** The learner can ask for a defense again whenever they feel ready, with no limit and no tally, and can pause one at any point. Distress stops any session (principle 18).
- **Checked every release:** the tutor's transcripts fail if it presses a parked question, paraphrases the learner in the record, or relays a result as a fail. The validator's fail if they read anything outside their allowed files or end without feedback for the tutor. The mentor's fail if it gives a step hint, sets a status, or ends without naming a next step.

**How pacing and course load are managed (v0)**

The aim is projects that stay relevant, a workload the learner finds right, and real growth they can feel. The organizer watches for that; the learner has the final say.

- **Signals the organizer reads:** active projects, steps drafted versus defended, time since the last defended step, hints per step, parked defense questions, diary entries, the tutor's struggle flags, and the learner's own feedback.
- **The learner steers.** At every check-in the learner is asked what they want to learn next, what's working and what isn't. Anyone can raise it at any time, and the organizer treats it as the most important signal.
- **Who the organizer consults:** the tutor on where the material isn't landing, and the mentor on whether a change still serves the learner's growth and the project's purpose.
- **What it can propose:** pausing a project, slowing the pace, adding remedial steps before a hard concept, swapping or reordering the next projects, or adding a project the learner asks for. Proposals are plain, short and optional. Nothing changes without the learner's yes, and the lesson planner makes the accepted change. Proposals reach the learner through the tutor, together in the end-of-session prompt.
- **When it runs:** at each check-in, on the learner's cadence, when the tutor flags struggle, when the learner falls behind their commitment, and whenever the learner asks.
- **Positivity is a signal too.** When the learner says the work feels good, the organizer keeps the pace and says why it's working.
- **Checked every release:** the organizer's transcripts fail if it changes a plan without the learner's yes, frames a slowdown as failure, or ignores feedback the learner gave.

**When the validator consults the mentor (v0)**

A wrong answer can still show real growth. Someone lost in procedure or definitions may be reasoning in a pragmatic, mature and thoughtful way; this is common in mathematics. The validator judges the work; the mentor sees the person's growth. The validator asks the mentor whenever it sees one of these:

- the same content problem recurring across attempts or steps, alongside thoughtful reasoning;
- an answer that is wrong or off the intended path but shows perspective, judgment or a sound instinct;
- any case where it can't tell whether a gap is about understanding or about procedure.

**How it works:** the validator writes a request naming the step, the gap, and the reasoning it noticed, quoting the defense record. The mentor reads that and the learner's trajectory, then writes a short reply: what growth it sees, whether the gap looks like procedure and definitions or like understanding, and what would help. The validator reads only the reply, so its context stays clean.

**What changes:** the three checks stay honest, and an incorrect answer is never marked correct. But the feedback leads with the growth the mentor named. Procedural gaps go to the tutor as targeted practice, and to the organizer as possible remedial steps, framed as building tools for thinking the learner already shows. Chronic gaps paired with strong reasoning are never read as lack of ability.

**Checked every release:** a transcript fails if the validator skips the mentor when a recurring gap comes with thoughtful reasoning, or if feedback for such a case omits the growth the mentor named.

## Workspace layout (v0)

Every file has exactly one home, decided by what it is. In v0 the harness writes its own files where they belong; tools for filing loose files come later.

```text
learning/                          # the learner's workspace, created by init_project
├── inbox/                         # loose files wait here; filing tools come later
├── projects/
│   └── <project-slug>/
│       ├── program.yaml
│       ├── commitment.md
│       ├── progress.yaml
│       ├── data/                  # inputs; one subfolder per source if more than one
│       ├── solutions/             # one file per step, with its follow-on problems
│       ├── work/                  # the learner's own; the harness never moves anything in it
│       └── portfolio/             # a portfolio addition, if the learner makes one
└── .private/
    ├── learner.yaml
    ├── proposals.yaml
    ├── diary/<yyyy>/<mm>/<yyyy-mm-dd>-<slug>.md
    ├── log/<yyyy>/<mm>/
    ├── attempts/<project-slug>/<step-id>/
    ├── handoff/<project-slug>/<step-id>/  # defense records and notes between roles
    ├── learnings/<project-slug>/
    └── index/                     # keyword index and TurboQuant vectors; rebuildable
```

- **One home per file type.** The file table under Program spec and learner state names each home; anything that matches none goes to `inbox/`.
- **Fixed files:** only these sit at a folder's top level: `program.yaml`, `commitment.md` and `progress.yaml` at a project root; `learner.yaml` and `proposals.yaml` in `.private/`; a single source's files in `data/`. Everything else lives one level down, by step, source or date.
- **Harness folders only:** the rules cover `inbox/`, `data/`, `solutions/`, `portfolio/` and `.private/`. The learner's `work/` is theirs to arrange (for example, one notebook for every step), so paths inside code and notebooks never break.
- **Names:** lowercase, hyphenated, no spaces; dated records start with yyyy-mm-dd.
- **Nothing is ever deleted** by the harness.
- **Later:** `check_layout` and `move_file` for filing inbox items (each move confirmed in the end-of-session prompt), and splitting folders that pass 25 files.

## Learner pipeline (v0, except where marked later)

Seven stages. Stages 1–5 run once, stage 6 repeats each week, and stage 7 closes the program.

1. **Project → solution.** The learner states a problem they want to solve (for example, "train a model that flags fraudulent support tickets"). The lesson planner lays out how a working solution is built, end to end: steps, components and the decisions at each step.
2. **Solution → concepts.** Each step is broken into the concepts it depends on. Where a standard describes what a step teaches, the plan cites it, so the learner sees what they are learning in recognized terms (in the default program's first project, fitting a line touches HSS-ID.C.7, for example). Standards annotate the project and supply prerequisites; they never set its scope.
3. **Concepts → plan.** Steps are ordered by what the project needs next. Each step produces a working piece of the project.
4. **Diagnose (later).** A short check on the prerequisites the plan relies on; gaps become short detours, not separate courses. In v0 the tutor talks prerequisites through in conversation.
5. **First check-in.** The learner chooses a cadence (weekly, irregular, or only when they ask) and, only if they want them, a deadline and a showcase date.
6. **Run, at the learner's cadence.** Work through steps with the tutor, see whatever helps, ask for a defense when ready, check in, adjust the plan. Practice sets come later.
7. **Finish.** Assemble a portfolio addition if the learner wants one, explain it in a defense if they choose, and share it wherever and whenever they decide.

## Skill inventory

Ten skills: six in v0, four later. The lesson planner, validator and archivist run as subagents; tutor, mentor and check-in run in the main thread.

| Skill | Runs as, when | Reads | Writes | Release |
| --- | --- | --- | --- | --- |
| design-from-project | Lesson planner subagent; stages 1–3, and when an accepted change needs a new plan, detour or remedial step | the learner's project goal, or a default-program project | `program.yaml`; `solutions/` with follow-ons (via `write_solution`) | v0 |
| tutor | Main thread; every session | current step, `learner.yaml`, notes for the tutor, learnings | attempts, reveals, defense records, session notes, seen and drafted status | v0 |
| validate | Validator subagent; when the learner asks for a defense | `work/`, the step, the step's handoff folder | questions, judgment and feedback via `post_note` and `set_status` | v0 |
| mentor | Main-thread mode; when the learner or a role asks, at check-in, at project end | notes for the mentor, learnings, `progress.yaml`, `program.yaml` | replies via `post_note`, session notes | v0 |
| check-in | Main thread (facilitator and organizer); at the learner's cadence | `commitment.md`, `progress.yaml`, learnings, notes for the organizer | `commitment.md` (cadence; optional deadline, showcase date and fallback), pacing and profile proposals | v0 |
| archive | Archivist subagent; at check-in | new diary entries and notes | learnings via `extract_learnings` | v0 |
| diagnose | — | `program.yaml` | `learner.yaml` (level, gaps), extra steps | later |
| practice | — | steps not yet defended | exercises in `work/`, review schedule | later |
| add-to-portfolio | — | `work/`, `progress.yaml` | `portfolio/` (artifact, write-up, a post the learner can publish) | later |
| organize | — | `inbox/`, the layout | filing and archive moves | later |

- **No grades or scores.** The test of learning is whether the learner can explain the work to someone who wasn't there, if they want to.
- **The validator never talks to the learner.** It judges from a clean context and gives feedback to the tutor, who runs the defense (see How a defense works). Nobody audits plans or generated material; that is `check_links` plus the learner's own judgment.
- **"Defended"** means the learner's reviewed record shows, in their own words, that they (1) explained what the work does and why, (2) worked through at least three of the validator's questions, including one about a path not taken, and (3) named one limit of their work. `set_status` refuses "defended" until all three are recorded. A defense is offered, never required, and can be asked for as many times as the learner likes.
- **On Codex:** subagent isolation rests on what the subagent is given, since there is no hook.
- **v0 total:** 6 skills, enough to run the default program from start to finish (a portfolio addition is assembled by hand in v0).

## Plugin architecture

One repo, two manifests. Claude Code is the tested harness for v0; the Codex manifest ships as experimental. The skills are shared unchanged; only the packaging differs per harness.

- **Skills are portable.** SKILL.md is an open standard ([agentskills.io](https://agentskills.io/specification)) supported by both Claude Code and Codex ([Codex skills docs](https://developers.openai.com/codex/skills.md)).
- **Claude Code** reads `.claude-plugin/plugin.json`, with `skills/`, `agents/` and `hooks/` at the plugin root ([plugin structure](https://www.mintlify.com/trailofbits/skills/contributing/plugin-structure)).
- **Codex** reads `.codex-plugin/plugin.json`, with `skills/` and an optional `.mcp.json` ([Codex plugin system](https://codex.danielvaughan.com/2026/04/21/codex-cli-plugin-system-building-sharing-reusable-agent-workflows/)). Agent Plugins 1.0 (Aug 2026) is a vendor-neutral packaging spec Codex supports ([overview](https://codex.danielvaughan.com/2026/08/08/agent-plugins-1-0-open-standard-codex-cli-portable-skills-mcp-packaging/)).
- **The difference that matters:** hooks and subagents don't port cleanly. So rules that must hold (every reveal paired with a follow-on problem, the defended checklist) are tool-gated by the core MCP server and backed by a Claude Code hook. On Codex the tools still gate the files, but no hook stops direct reads, which is one reason Codex stays experimental. Skill instructions explain the rules; hooks are an extra layer on Claude Code only.

```text
education-harness/
├── .claude-plugin/plugin.json      # Claude Code manifest
├── .codex-plugin/plugin.json       # Codex manifest (experimental)
├── skills/
│   ├── design-from-project/
│   │   ├── SKILL.md
│   │   └── assets/program.template.yaml
│   ├── tutor/SKILL.md
│   ├── validate/SKILL.md
│   ├── mentor/SKILL.md
│   ├── check-in/SKILL.md
│   └── archive/SKILL.md
├── agents/
│   ├── lesson-planner.md            # subagent: writes plans and solutions out of the tutor's sight
│   ├── validator.md                 # subagent: clean context, never talks to the learner
│   └── archivist.md                 # subagent: learnings and search, at check-in
├── hooks/                           # best-effort read and edit guards
├── mcp/                             # core MCP server (Python, stdio)
├── tests/transcripts/               # regression conversations per skill
├── programs/data-scientist/         # the default program
│   ├── track.yaml                   # its projects in order, with standards mapped
│   └── <project-slug>/              # program.yaml, solutions/, data/ and a rebuild script
├── templates/.gitignore             # ignores .private/ in the learner's workspace
├── PRINCIPLES.md
├── INSTALL.md                       # pinned to a release tag, with a preflight check
└── AGENTS.md                        # shared instructions for both harnesses
```

## Program spec and learner state

Everything lives as plain files in the learner's workspace, `learning/`, laid out as in Workspace layout; paths here are relative to it. The core MCP server only reads and writes them. Files are split in two: project files can be published, and everything under `.private/` (profile, proposals, log, diary, attempts, handoffs, learnings and the search index) is git-ignored by default and never pushed. Diaries can hold notes about several people and about access needs, so they stay private unless the learner moves them out. Every YAML file carries a `schema: 1` field so later versions can upgrade forks.

| File | Holds | Written through | Private |
| --- | --- | --- | --- |
| `projects/<slug>/program.yaml` | the project question, steps, concepts, optional standards cited, what a strong version of each step shows, constellation | lesson planner | no |
| `projects/<slug>/solutions/` | hints, worked solutions and follow-on problems per step, pre-written for default-program projects | `write_solution`; served by `reveal_solution` | no |
| `projects/<slug>/commitment.md` | cadence, and an optional deadline, showcase date and fallback plan | check-in | no |
| `projects/<slug>/progress.yaml` | per-step status (not started, seen, drafted, defended) and what was revealed | `set_status`, `reveal_solution` | no |
| `projects/<slug>/data/` | inputs | `init_project` (default program) or the learner | no |
| `projects/<slug>/work/` | the learner's work, arranged as they like | the learner | no |
| `projects/<slug>/portfolio/` | a portfolio addition, if the learner makes one | the learner | no |
| `inbox/` | loose files waiting to be filed | the learner | no |
| `.private/learner.yaml` | access needs, preferences, formats that fit, areas to grow, whether they work alone | `propose_profile_change` (learner accepts) | yes |
| `.private/proposals.yaml` | intake answers and pending proposals | `propose_profile_change` | yes |
| `.private/attempts/<slug>/<step-id>/` | the learner's work, questions and follow-on work | `record_attempt` | yes |
| `.private/handoff/<slug>/<step-id>/` | defense records the learner reviewed, and notes between roles | `record_defense`, `post_note` | yes |
| `.private/log/` | session notes | `log_session` | yes |
| `.private/diary/` | optional diary entries | `add_diary_entry` | yes |
| `.private/learnings/<slug>/` | learning records linked to their sources | `extract_learnings` | yes |
| `.private/index/` | keyword index and TurboQuant vectors | every write tool; rebuildable from the files | yes |

```yaml
# program.yaml (shape, abbreviated): idea 2 of the default program, for a learner who ages cheese
schema: 1
track: data-scientist              # the default program; absent for a learner's own project
idea: 2                            # training is walking downhill on a loss
project:
  question: How fast does a wheel of cheese lose water as it ages?
  example: 8 weekly weights of one wheel, in grams   # tiny, from the learner's interests
  interests_used: [cheesemaking]
steps:
  - id: s2
    does: fit an exponential decay by walking downhill on the squared error
    concepts: [exponential decay, squared error, gradient]
    standards_cited: [CCSS.HSF-LE.A.2, CCSS.HSF-LE.A.4]   # optional reference points only
    format: solve-it
    strong_version_shows: [the loss written out, one gradient step by hand, the rate explained in context]
    requires: [s1]
constellation:
  history: How did cheesemakers judge aging before scales and thermometers?
```

## Learning loop

The harness learns how each person learns, and keeps learning it. It starts from what the learner says they need, then adjusts from evidence: what they solved, where they got stuck and how their defenses went, with the diary as context. **v0:** intake, two problem formats, the diary and learner-approved profile changes. Pairs, groups, the guardian mode and the other formats are **later**.

1. **Intake.** A short conversation, not a test, in three parts. **Access needs first:** anything that makes a format hard or impossible, such as difficulty reading long text, and these are always honored. **Preferences second:** how the learner likes to take things in (reading, seeing, doing, building, talking it through), treated as a starting point to test, not a fixed label. Interests third: what the learner cares about, from a short interview or from a photo, resume or documents they choose to share (see Interests at setup). The tutor states that it works in text, and offers short text, diagrams and spoken walkthroughs where the harness supports them.
2. **Lessons meet access needs, then test preferences.** Access needs are always met, for example short text, diagrams and step-by-step worked examples for someone who struggles with long text, with spoken walkthroughs only where the harness supports audio. Beyond that, the tutor offers the learner's preferred format first, always pairs it with a second one, and keeps whichever the results show working.
3. **Diary.** After a session the learner can write or dictate a line or two: what clicked, what didn't, which format helped. It is offered in one question, can be skipped, and is never a condition of anything.
4. **Update.** `check-in` reviews the record since the last check-in (solved or stuck, defense results, diary) and proposes changes to `.private/learner.yaml`. The learner accepts or edits them; nothing changes silently. Self-report counts, but results count more.
5. **Feed the harness.** Everything stays in the learner's local copy, and the diary keeps improving their own harness over time. Learners who want to change the harness itself fork the repo and modify their own copy. The main repo stays a general-purpose harness and is not tuned to any one learner's diary.

The profile is a starting point, never a fixed label: if the diary shows a different format working, the harness follows the evidence.

**Problem formats: what is masked (v0: Solve it and Work backward)**

Lessons vary what the learner sees, so they don't always move through a problem the same way.

| Format | Shown | Masked | The learner |
| --- | --- | --- | --- |
| Solve it | The problem | The method and the answer | Works it out from scratch |
| Work backward | The problem and the answer | The method | Finds a way to reach the known result |
| Fill the gaps | Part of the method, part of the answer | The rest | Completes a partly worked solution |
| Many paths | The problem | Nothing fixed | Solves it two or more ways and compares them |
| Many answers | An open problem | No single right answer | Proposes an answer and defends why it fits |

- `tutor` rotates formats across a project; **v0 uses two, Solve it and Work backward**, and the rest come later. After each one, the diary records how it went: solved or stuck, which path the learner took, how long, and how it felt.
- **What the harness learns:** `check-in` reads the entries at each check-in and proposes updates to `learner.yaml` with two lists: formats that fit this learner (for example, "works backward well from a shown answer"), and opportunities to improve (for example, "stalls on open problems with many answers").
- **How it acts on it:** strengths are used to introduce new concepts; improvement areas are practiced on purpose, in small doses, so the learner grows instead of staying only where they're comfortable. The learner sees both lists and can correct them.
- `defend` asks about the path taken, not only the result: why this way, and what another way would have changed.

**Working toward understanding, together (v0)**

The tutor works alongside the learner toward an understanding of how something works. There is no moment where the learner either knows it or doesn't, and no test to pass before help arrives. It is a conversation between two people figuring something out.

- **Open the conversation, not a test.** The tutor offers ways in: "Want to talk through how you think this works?", "Shall we start from what the problem is actually asking?", "What do you notice in the data?" The learner's current picture, a restatement of the problem, a hunch, a question, or "let's look at it together" are all real contributions, and each is saved as their work on the step.
- **Showing is part of working together.** When the learner wants to see the answer or the method, the tutor shows it and keeps going with them. With the answer in view, they work out together how one gets there; the method stays to be discovered. With the method in view, they carry it to a sibling problem (other numbers, data or context), where the solution becomes something the learner now knows and can use.
- **Language is social, never confrontational.** No "try it first", "take a guess", "test yourself" or "do you know". Prompts are invitations to think together: "let's see", "what would happen if", "how would you explain this to a friend". A guess is welcome when the learner offers one, and the tutor explores where it came from, but it is never asked for as a price of help.
- **Status follows the follow-on.** A step is drafted once the learner has worked through its follow-on problem; defended counts the learner's own work on a problem they hadn't seen solved.
- **Follow-ons come from the plan.** Each step in `solutions/` carries at least two follow-on problems: pre-written for the default program, written by the lesson planner through `write_solution` for other projects.
- **What was shown is evidence, not a mark.** The diary records what the learner chose to see and what the follow-on taught, so the harness learns where to teach differently.
- **Checked every release:** the tutor's transcripts fail on confrontational framing (asking for a guess before helping, "do you know", know-it-or-don't choices) and on any shown solution without its follow-on.

**What matters, and the space around the learner (v0)**

The tutor makes one thing plain, early and whenever it helps: having the answer doesn't really matter, and neither does finding the one method to it. What matters is that learning happens, in the setting where it can happen most positively, and that the learner grows. Standardized tests aren't valuable in themselves; being informed and able to think for oneself is better for the person and for the society they live in.

- **Offer another shape.** When a problem isn't opening up, the tutor offers to structure it differently (a smaller case, a picture, a story, the problem told backward) or to lay the solution out as a dialogue the two of them can question piece by piece, so they can explore an alternative together.
- **Tune into the learning environment.** Often the obstacle isn't the material: it's a noisy or rushed setting, no routine, or no structure and no way yet to build one. The tutor notices the signs (short broken sessions, "I can never focus on this"), asks gently, and helps build the structure: a set time and place, a smaller session, a checklist for getting started. Patterns go to the organizer for pacing and to `learner.yaml` as a proposal the learner accepts.
- **Other people are part of learning.** The tutor lets the learner know it is encouraged to talk the problem over with someone: a person with more experience, who may see the situation more maturely, or another learner, to whom they can try explaining how it works. Explaining to someone else is one of the best ways to understand.
- **Mentioned, never pushed.** It comes up once at intake, then only when it would clearly help, such as a problem that would benefit from another view, and at most once a project otherwise. If the learner says they are on their own, that is recorded and respected: the agents are their thinking partners, and the subject comes back only if the learner raises it or their situation changes.
- **Checked every release:** the tutor's transcripts fail if it raises other people more than the rules allow, or after the learner has said they work alone.

**Pairs and groups (later)**

A session can include more than one person. The tutor facilitates the group, and each person takes a role in the learning.

| Setup | Who | How the AI facilitates |
| --- | --- | --- |
| Solo | One learner | Tutor, as above |
| Pair | Two learners | Assigns roles (for example, one drives, one questions), swaps them, and asks each to explain the other's step |
| Group | Three or more | Splits the problem, gives each person a role (builder, checker, skeptic, explainer), and brings the parts together |
| Learner and guardian | A learner (often a minor) and a parent or guardian | Treats both as participants, with distinct roles (below) |

**Learner and guardian (later, after checking each model provider's age terms)**

- **The guardian is challenged too.** They get their own prompts and problems, and they don't need to know the answer. Working it out alongside the learner is welcome.
- **Clear roles, flexible mix.** The learner owns the project and the work. The guardian's default role is co-solver and questioner; they can also be a fellow learner, a coach, or an observer. The AI states the roles at the start of each session and keeps to them, and the pair can change them whenever another mix would help the learner more.
- **Sensitive to the dynamic.** The AI never sets the adult and learner against each other and leaves room for the learner to lead. A wrong answer from either person is treated the same way as any other: as an opportunity to learn more (below).
- **Shared diary.** Each entry records what both people learned, in their own words, plus how they worked together.

The diary and the learning profile track each person's role, so the harness learns which setups and roles work best for this learner.

**Guesses and mistakes (v0)**

No one is "wrong" in the harness. Learning is a scale, and an incorrect answer marks a place to learn more. The harness says "not yet" and "what led you there?", never "wrong".

- **Guessing is welcome.** When the learner offers a guess, the AI explores where it came from, as one way into understanding: what the person already knew, and what pattern they matched. It never asks for a guess as a condition of help. Example: guessing a dolphin is a fish because it lives in water and swims, then investigating why breathing air and nursing young make it a mammal.
- **Guessing as a strategy.** Some guesses are tools, not hunches: halving the search space with each guess (bisection, binary search) finds an answer in very few steps. The harness teaches when guessing is efficient and why.
- **The diary keeps the reasoning.** Each entry records the guess, where it came from, and what changed after investigating it. Over time, this shows the harness how each person reasons and where their understanding is growing, which it uses to shape later lessons.
- **Plain about correctness.** "Not yet" is never vague: the tutor always says clearly that an answer doesn't hold yet, shows where it breaks, and then asks what led there.

## Accountability mechanics (v0)

The learner holds themselves accountable, in their own way. Every mechanism here is offered, never imposed, and the learner can switch any of them off.

| Mechanism | How it works | Skill |
| --- | --- | --- |
| A clear project | The learner knows what they're working toward before lessons begin, and can change it at any time | design-from-project |
| Specific plans (optional) | Sessions with a when, a where and a length, if the learner wants them | check-in |
| Planned recovery (optional) | A fallback the learner sets in advance, e.g. "if I miss a session, I do a 15-minute version the next day" | check-in |
| Showcase date (optional) | A date the learner may set for sharing their work; theirs to set, move or drop | check-in |
| Check-in at the learner's cadence | Planned vs. actual, weekly, irregular or only when the learner asks; after missed sessions it offers a smaller plan, which changes only with the learner's yes | check-in |
| Defense (offered) | The learner explains the work and works through the validator's questions with the tutor, so they can explain it to anyone; step-level threads go back to the tutor, bigger questions to the mentor | tutor, validate |

## Default program (v0): How to be a data scientist

The first program, offered by default. It is a path of six ideas, from high-school math to understanding how a transformer works, and it carries no examples of its own: every step is built around a very small example drawn from the learner's own interests. The program is an offer, not an expected path: the learner's aims come first (principle 0), and a learner with their own project can skip it or dip into one idea when their plan needs that math.

| # | Idea | Math it needs | Standards it touches | A tiny example might be |
| --- | --- | --- | --- | --- |
| 1 | A model is a function fitted to data | Variables, scatter plots, linear functions, slope as a rate, correlation vs cause | HSF-LE.A.1b, HSS-ID.B.6, HSS-ID.C.7, HSS-ID.C.8, HSS-ID.C.9 | Minutes practiced vs. songs learned, over 8 weeks |
| 2 | Training is walking downhill on a loss | Exponential and log functions, squared error, minimizing a function of two variables, partial derivatives, the gradient | HSF-LE.A.2, HSF-LE.A.4, HSF-IF.C.8b, HSF-BF.B.5 (+); calculus outcomes written by the program | A cheese wheel losing water weight week by week |
| 3 | Classification as a probability | The logistic function, probability, conditional probability, log-loss, train and test | HSF-IF.C.7e, HSS-CP.A.2, HSS-CP.A.3, HSS-CP.B.6, HSS-IC.B.5 | Will the bus be late, from a dozen past trips |
| 4 | Meaning as direction (embeddings) | Vectors, distance, the dot product, the angle between vectors, cosine similarity, nearest neighbors | 8.G.B.8, HSG-SRT.C.8, HSN-VM.A.1, HSN-VM.A.3, HSN-VM.B.4, HSN-VM.B.5 (+); the dot product written by the program | Five favorite recipes as ingredient vectors |
| 5 | A feed-forward network and backpropagation | Matrices, matrix-vector products, function composition, exponentials in softmax, the chain rule as partial derivatives of nested functions | HSN-VM.C.6, HSN-VM.C.8, HSN-VM.C.11, HSN-VM.C.12 (+), HSF-BF.A.1c (+); the chain rule written by the program | A tiny network sorting a dozen points the learner picked |
| 6 | A transformer small enough to trace by hand | Embeddings; positional encodings from sine and cosine at many frequencies (periodic functions, the unit circle); attention as scaled dot products; softmax and cross-entropy (exponentials and logs); matrix products through the stack; sampling | HSF-TF.A.2, HSF-TF.B.5, HSN-VM.C.8, HSN-VM.C.11 (+), HSS-MD.A.1, HSS-MD.A.2 (+); attention written by the program | Attention across a four-word sentence from the learner's own writing |

- **Tiny, personal examples.** The lesson planner builds each step around 5 to 20 numbers (or a handful of words or vectors) from what the learner cares about, small enough to work by hand or in a few lines of code. The same example can carry across ideas when that helps, so the learner meets new math in a setting they already know.
- **The examples are the learner's to change.** If an example doesn't land, the tutor offers another from a different interest. A learner who wants to can swap in real data they bring; it is never required.
- **Built to understand:** ideas 2, 5 and 6 are built in NumPy before any library.
- **Standards:** `track.yaml` lists each step's standards from Common Core high-school math (via Learning Commons) and its Statistics and Probability standards; (+) marks Common Core's advanced standards, and 8.G.B.8 is the grade-8 distance formula. Calculus, the dot product and attention have no Common Core codes, so the program writes those few outcomes itself and labels them. Every code is checked before release.
- **Detours, not courses:** when a step needs math the learner lacks, the tutor asks the lesson planner for a short detour inside the step. A learner returning to the math, for example to understand backpropagation and transformers end to end, can start at any idea: the tutor talks through what they remember and suggests where to begin.
- **Generated, then checked.** Solutions and follow-on problems are written for each learner by the lesson planner, out of the tutor's sight. Every number in them is computed by running code before it is saved (principle 7), and the validator runs the learner's code before anything is called correct.
- **No idea where to start?** A few one-line suggestions are offered (for example, whether shadier streets are cooler, or how fast a used car loses value), never assigned.

### Interests at setup (v0)

At setup, after access needs and preferences, the facilitator learns what the learner cares about, in whichever way the learner prefers:

- **An interview:** a few open questions: what they do for work, what they do with free time, who they help or would like to help, something they've always wanted to understand or make. Any question can be skipped.
- **Something to show:** a photo, a resume or a few documents the learner chooses. The facilitator reads them in the session and proposes a short list of interests, which the learner edits.
- **What's kept:** only the list of interests the learner accepts, saved to `.private/learner.yaml` through the usual proposal step. The photo, resume or documents are not copied into the workspace unless the learner asks, and the README says plainly that anything shared in a session goes to the model provider.
- **Other people:** if a document names other people, their details are not kept.
- **Revisited:** interests can be added or dropped at any check-in, and the examples follow.

## Job analysis data (later)

The adult curricula are anchored in two market datasets. Postings pulled from companies' public job-board APIs show what employers ask for now; Live Data Technologies shows how people actually move into each role. O\*NET and EDISON stay the open structure that both get mapped onto.

| Source | What it tracks | Question it answers | Use in curricula |
| --- | --- | --- | --- |
| Public ATS job-board APIs: [Greenhouse](https://developers.greenhouse.io/job-board.html), [Lever](https://github.com/lever/postings-api), [Ashby](https://developers.ashbyhq.com/docs/public-job-posting-api) | Published postings, with full descriptions, at any company whose board is public; no key needed. Company list guided by TrueUp's public rankings (Hot 200, AI 50) | What skills and tasks do postings for this role ask for, at each level, and how is demand trending? | Pick and weight outcomes; set depth tags; choose which roles to seed first |
| [Live Data Technologies](https://coldiq.com/apis/live-data-technologies-api) | Job changes for 160M professionals, with job history, plus function and level derived from title ([field list](https://docs.google.com/spreadsheets/d/1zcPrqjv9HtDs0l43teLgWPLlBOgFS26Np-5mB6zYKSQ/edit)) | What roles do people hold before they become a data scientist or PM, and how long does the move take? | Design on-ramps by starting role; choose prerequisite modules; check which depth matches which level |

**Pipeline, refreshed quarterly**

1. Pull postings for each of the 5 roles from the public ATS APIs of a fixed company list (a few hundred tech companies), split by level.
2. Extract skills and tasks from posting text with a model; normalize each into our own skills taxonomy, cross-walked to O\*NET and EDISON.
3. Weight outcomes by how often they appear and how fast they are growing. Outcomes common in entry-level postings become light; those mostly in senior postings become deep.
4. From Live Data, compute transition paths into each role (prior title and function, time between roles). Turn the most common paths into on-ramp variants, e.g. analyst → data scientist, or program manager → product manager.
5. Diff each refresh against the last and publish a curriculum changelog.

**Constraints**

- **Licensing:** TrueUp publishes reports and rankings but no data feed, so it serves only as a reference for which companies to include (a data deal would need direct contact). The ATS APIs are public; use postings only in aggregate and honor each provider's and employer's terms. Live Data sells API access commercially. Confirm its contract allows publishing aggregate findings inside openly licensed curricula.
- **Privacy:** Live Data is person-level data. Use aggregates only (counts, transition shares, with a minimum group size); no names, profiles or contact fields ever reach a curriculum or a learner.
- **Coverage:** The company list decides coverage: keep it to tech companies, which fits the target roles. Live Data's function and level are model-derived from titles, so treat them as noisy.

## Concept maps and seed tracks (later)

There is no fixed curriculum: each one is generated from the learner's project. The seeds are worked examples, a few typical projects per role with their solution already broken into steps and concepts, so learners can start from one or use it as a model for their own. The role and course maps below are the concept maps that generated plans draw on. Two tracks: adult tech roles and high-school math courses.

**Variants: three depths × two durations, generated rather than hand-written**

Depth sets how far down the stack the learner goes, not which topics or models they may study. Any topic (classical ML, deep learning, transformers) can be taken at any depth; the learner picks the topics, then the depth and the duration. Each outcome in a competency map is written three ways, once per depth.

| Depth | Level of abstraction | Example: transformers | Portfolio addition |
| --- | --- | --- | --- |
| Light | Use out-of-the-box Python packages; know what each step does and when to use it | Fine-tune and evaluate a pretrained model with Hugging Face | A working project built with standard packages, explained in plain terms |
| Medium | Configure and adapt the components: custom training loops, losses, tuning, reading the architecture | Write a PyTorch training loop; swap heads, losses and tokenizers; diagnose failures | A project that changes the defaults on purpose and defends each change |
| Deep | Build the pieces from scratch to understand the math | Implement attention and a small transformer in NumPy, with backprop by hand | A from-scratch implementation checked against a library version |

| Duration | Pacing (proposed) |
| --- | --- |
| Short | Same outcomes, compressed: about 4–6 weeks at higher weekly hours |
| Extended | Same outcomes, spread out: about 12–16 weeks at lower weekly hours, more practice and review |

**Adult track: tech roles**

| Curriculum | Competency sources | Example deep portfolio addition |
| --- | --- | --- |
| Product management | Product manager postings from public ATS boards as the primary source (no dedicated O\*NET occupation); O\*NET adjacent occupations for structure | Discovery-to-spec for a real product problem: research, PRD, metrics, launch plan |
| Program management | O\*NET Project Management Specialists (13-1082.00) | Cross-team program plan: scope, dependencies, risks, status cadence, retro |
| Data analytics | O\*NET Business Intelligence Analysts (15-2051.01); EDISON data analytics area | Dashboard and written analysis answering a stakeholder question with public data |
| Data science | O\*NET Data Scientists (15-2051.00); EDISON CF-DS and DS-BoK | End-to-end model: framing, data, model, evaluation, written limits |
| Applied science | O\*NET Computer and Information Research Scientists (15-1221.00); EDISON | Reproduce a published result, then extend it, with an experiment write-up |

**High-school track: math courses (minors, guardian-supervised)**

| Curriculum | Standards source |
| --- | --- |
| Algebra I | Common Core HS math via Learning Commons, traditional course pathway |
| Geometry | same |
| Algebra II | same |
| Precalculus | same (advanced standards) |
| Statistics | Common Core HS Statistics and Probability; the reference case comes from here |

An integrated pathway (Math I–III) can be generated from the same standards later.

**Hybrid: Math for Machine Learning (AP-level)**

A sixth high-school curriculum that takes from each course only what classical ML, deep learning and transformers need. Its adult form ships in v0 as the default program; this later version adapts it for minors working with a guardian. There is no College Board AP Data Science course; the new AP courses for 2026–27 are [Business with Personal Finance and Cybersecurity](https://testing.fulbright.or.kr/en/?p=11447). "AP" is a College Board trademark, so describe this as AP-level and keep "AP" out of the product name.

| Strand | Taken from | Concepts | Used for |
| --- | --- | --- | --- |
| Functions and models | Algebra I and II | Linear, polynomial, exponential and log functions; function composition; summation notation | Linear regression, log-loss, softmax, model as a function |
| Vectors and distance | Geometry, Precalculus | Coordinates, distance formula, vectors, dot product, angle between vectors | Nearest neighbors, cosine similarity, embeddings, attention scores |
| Matrices | Precalculus (advanced standards) | Matrix multiplication, matrices as transformations | Feed-forward passes through network layers, attention as matrix products |
| Probability and statistics | Statistics | Distributions, conditional probability, expected value, regression, correlation, train/test thinking | Classification, evaluation, overfitting, sampling |
| Rates of change | Calculus (beyond Common Core) | Partial derivatives and the gradient only; the chain rule appears as partial derivatives of nested functions | Gradient descent, backpropagation |

| Topic (learner picks any) | Light | Medium | Deep |
| --- | --- | --- | --- |
| Linear and logistic regression | scikit-learn fit, predict, evaluate | Regularization, feature engineering, reading coefficients | Closed-form and gradient-descent fits in NumPy |
| Trees and gradient boosting | XGBoost with default settings | Tuning, feature importance, overfitting control | A decision tree and a small boosting loop from scratch |
| Neural networks | Keras or PyTorch high-level APIs | Custom PyTorch training loop | Feed-forward and backprop in NumPy |
| Transformers | Hugging Face pipelines and fine-tuning | Modify architecture, tokenizer and training | Attention block from scratch |

- **Calculus** is limited to partial derivatives, alongside matrix multiplication from the Matrices strand. It has no Common Core standards, so we write these few outcomes ourselves. OpenStax Calculus is [CC BY-NC-SA](https://openstax.org/books/calculus-volume-1/pages/index), non-commercial only: link to it, don't bundle it.
- **Prerequisite routing:** the diagnostic sends learners back into the full course maps for any strand they're missing, so the hybrid stays short.

**Open-source licensing (v0)**

- **The project is open source and non-commercial.** An individual, not-for-profit side project with no paid tiers, ads or sponsorship. Any income comes only from the maintainer's own social media, kept separate from the project, and that content uses only the project's own CC BY material, never non-commercial sources.
- **Code (skills, plugin, scripts):** MIT license.
- **Core curricula:** CC BY 4.0, built only on public-domain or CC BY sources: [O\*NET](https://www.onetcenter.org/license_db.html), [EDISON](https://zenodo.org/records/167585/files/EDISON_CF-DS-release1-v07.pdf), Learning Commons, Illustrative Mathematics, and OpenStax titles that are CC BY (check each; Calculus is not).
- **Courseware is referenced, not bundled:** MIT OpenCourseWare, CS50 and OpenStax Calculus appear only as links. The tutor generates its own explanations and exercises on the same topics; it never reproduces their lectures or problem sets.
- **Leave out:** SFIA (its free licenses exclude commercial exploitation and bar redistribution) and proprietary courses or certificates. Topic coverage can still be modeled; their materials can't be copied.

## Constellation: adjacent domains (v0: the seed's hand-checked set only)

Every project is shown with its constellation: the adjacent domains that give the work perspective. Six domains, always visible: literature, history, ethics, law, sociology and philosophy. The project stays the core; the constellation is how broad education branches off it.

| Domain | Example: a model that flags fraudulent support tickets |
| --- | --- |
| Literature | Kafka's *The Trial*: being judged by a process you cannot see |
| History | How credit scoring and actuarial risk models grew, and what they excluded |
| Ethics | The cost of a false flag vs. a missed fraud, and who bears each |
| Law | Rules on automated decisions, data privacy and the right to contest a decision |
| Sociology | Who gets flagged, and how bias enters through the labels |
| Philosophy | What counts as evidence; the problem of induction |

- **How it appears:** `design-from-project` writes one question per domain into the plan (readings only in hand-checked sets, such as the seed's, in v0), and the tutor raises them at the step they bear on.
- **Optional depth (later):** a learner can follow any domain into its own short study, which produces its own portfolio addition, such as an essay, defended like any other work.
- **In v0:** a `constellation:` field on each project with six questions; the seed also carries six hand-checked readings. Deeper study in the domains comes later, grown from the projects people actually choose.

**Preferred sources for constellation readings (for hand-checked sets in v0)**

Public-interest institutions and open, community-run projects come first, cited by link with short quotes.

| Source | Best for | Reuse |
| --- | --- | --- |
| United Nations documents (UN Digital Library, Universal Declaration of Human Rights, UNESCO Recommendation on the Ethics of AI) | Ethics, law, sociology | Documents issued under a UN symbol are generally public domain ([UN policy](https://en.wikisource.org/wiki/ST/AI/189/Add.9/Rev.2)); UN websites allow personal, non-commercial copying. Link, quote short extracts, never use the UN emblem |
| International Court of Justice judgments and advisory opinions | Law, history | Public full text; check the court's terms of use before quoting at length, and link otherwise |
| Wikipedia and Wikisource | All six domains, as a starting point | Wikipedia text is CC BY-SA, so link to it; adapted text would have to stay ShareAlike |
| Other open projects (Project Gutenberg for public-domain literature, OpenStax Sociology) | Literature, sociology | Public domain or CC BY; check each title |

Later, once readings are generated: the tutor pairs a general source (Wikipedia) with a primary one (a UN document or an ICJ opinion) where it can, so learners see both a summary and the original.

## Where the work leads (v0: the framing; product track later)

Self-growth points somewhere, and the learner chooses where. In *Democracy and Education*, Dewey treats vocation broadly: any occupation that joins a person's abilities to service to others, in the family, the community and work alike, not narrow job training. The harness follows that. A project can lead in many directions, and none of them is a north star; a project done for understanding alone is complete.

- **Helping someone close:** a parent, a sibling, a friend. For example, a budget model for a parent, or the same math explained to a younger sibling.
- **Helping the community:** an analysis a neighborhood group, school or local organization can use, such as a tree-cover map for a block association.
- **Preparing for what's next:** college, a course, a new job or an interview, with the portfolio addition as evidence of what the learner can do.
- **A product or business:** something that delivers value to others and tests the learner's judgment about people and markets.
- **The mentor helps find the direction.** At the end of a project, or when the work looks useful beyond itself, it asks who this could help and what it would take for one real person to use it, and it names where the work points (a course, a role, a community need). Putting the work in front of one person who might use it, and listening, is the smallest step outward, and it brings other people into the learning without pressure.
- **In the default program:** each project's portfolio addition names one optional way it could help someone, offered as a possible next project.
- **The constellation still applies:** who benefits, who could be harmed, what rules apply.
- **Later:** a product track built from the product-management concept map (talking to users, framing what's offered, a small launch), with the product defended like any other work.
- **The harness takes nothing.** Whatever the learner builds and earns is theirs (principle 13).

**Direction in a time of AI (v0)**

Many learners are anxious that AI will take their jobs, and unsure whether what they learn will be obsolete by the time they use it. The harness takes that seriously.

- **Make room for it.** When the learner raises it, or the diary shows the worry, the mentor talks it through. It neither dismisses the worry nor feeds it, and it is honest that nobody knows exactly which tasks will change.
- **Aim at what lasts.** The harness never aims at a single tool or skill. It aims at what Dewey calls reflective thinking: framing a problem, learning something new, judging evidence, explaining to others and working with people. Each project's write-up names the lasting capacity it built, not only the tools it used.
- **Learn with AI, not against it.** The learner already uses AI as a thinking partner in the harness, and each defense shows an understanding the AI can't supply for them. That combination is the point.
- **Direction is chosen and revisable.** The learner's aims are revisited at check-in, so a change in the job market becomes a change of direction, not a dead end.
- **Facts, not fear.** When the conversation turns to jobs, the mentor cites sources and labels uncertainty (principle 7), and never presents a forecast as certain.
- **Care first.** If the worry becomes distress, the session stops for it (principle 18).

## Pilot plan and metrics

Run 5 adults for 6 weeks. Each chooses their own project, which is what the hypothesis tests; anyone without one starts the default program. Targets are set now, before anyone starts.

| Metric | Definition | Target (of 5) |
| --- | --- | --- |
| Activation | `program.yaml` created in session 1 | 5 |
| First understanding | Within 7 days, the learner reports something they now understand (at check-in or in the diary) | 4 |
| Sustained work | Sessions logged in at least 3 of weeks 1–4 | 3 (the deciding metric) |
| Completion | A project finished, by the learner's own account, by the end of week 6 | 3 |
| Defense and sharing | Defenses asked for; work shared | recorded, no target |
| Usefulness | Learner rating, 1–5, at week 2 and the end | median 4 or higher |
| Effort and cost | Session hours per week for everyone; API spend for those on API access | recorded, no target in v0 |

- **Data source:** the learner's project files and, with their consent, a short summary from each `check-in`. Private files stay with the learner.
- **Qualitative:** a 20-minute interview at week 1 and week 6. Where did they stall, what did they ignore, what did they want that the skills didn't do?
- **Recruiting:** recent grads and career changers with a code or data project in mind (non-code projects come later).
- **Kill rule:** if fewer than 3 of 5 meet the sustained-work target, the self-run premise fails for v0. The interviews say why and what to change.

## Scope, open questions and build sequence

**Scope:** the v0 table near the top is the only definition of what ships. Everything tagged later waits until the pilot passes.

**Open questions**

- Do Anthropic's and OpenAI's terms allow under-18 users at all, and on what conditions? This decides whether the minors and guardian designs can ever ship on these harnesses.
- Is the current Codex plugin format confirmed against OpenAI's own documentation? The outline's Codex details come partly from third-party write-ups.
- Is `turboquant-py` stable enough to pin, or does the server carry its own NumPy implementation? Decided in build step 1.
- Every standards code in the default program is checked against Learning Commons before release.
- Should the six constellation domains stay fixed for every project, or should questions arise from each project's own steps?
- Which local model to list as experimental in the tested-on matrix.
- Does a person (you, or a peer) also hear pilot defenses, alongside the validator's review?

**Build sequence**

1. **Core MCP server (done):** the thirteen project tools, the best-effort hook and a self-check, each tool tested against files on disk; keyword search; the semantic opt-in (pinned model, TurboQuant storage, background install), tested on the maintainer's Mac.
2. **Default program path:** `track.yaml` with the six ideas, their concepts, prerequisites and standards; the lesson planner's rules for tiny examples, tested against a set of sample learner interests (every example small enough to work by hand, every number computed by running code).
3. **tutor, validate and mentor** SKILL.md, the validator subagent with its file allowlist, `record_defense` and `post_note`, run end to end on the first idea with an example built from a sample learner's interests, with their regression transcripts.
4. **check-in** SKILL.md (the intake interview including interests, cadence, pacing proposals, the end-of-session prompt), with transcripts.
5. **design-from-project** as the lesson-planner subagent, tested on the default program and on two learner-chosen projects until the output is stable.
6. **archive** skill and archivist subagent; headless transcript runner, passing in Claude Code.
7. **Ideas 5 and 6 end to end:** backpropagation and a small transformer built in NumPy from tiny examples, tested on several sample interests.
8. **Packaging:** Claude Code manifest, experimental Codex manifest, `AGENTS.md`, `INSTALL.md` pinned to a tag with its preflight check, `.gitignore` template; install and run end to end on a clean machine.
9. **README:** what it is, who it's for, cost, where conversations go (including anything shared at setup), tested-on matrix, install only from the main repo.
10. **Dry run** yourself, then three pre-release testers (two on the default program with their own interests, one on their own project) to pass the v0 acceptance tests.
11. **The 5-person pilot.**

**Later:** concept maps with depth versions, more default programs, one per role, the job-data pipeline, the minors and guardian designs, pairs and groups, distress handling for group and minor sessions, and non-code projects.
