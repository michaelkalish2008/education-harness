# Education Harness

**A learning companion with one clear doorway: say “Let’s learn.”** You can also say **“Teach me…”**, **“Show me the data-science path”**, **“Let’s go”** to continue, or **“Where am I?”** You do not need to know any commands, tools, skills or plugin terminology.

A free, open-source, Dewey-style learning harness for **Codex, Claude, ChatGPT Work and Claude Code**. It adds what an AI assistant doesn't keep on its own: **your place** across breaks and chats, **your own words** brought back when they matter, and **a goal** your work points toward. Everything else—explaining, adapting and drawing a picture—is the assistant doing what it already does well.

**Standards-grounded:** the default data-science path is mapped to academic standards. When standards data is loaded, the harness checks relevant prerequisites against standards supplied through the **Chan Zuckerberg Initiative Education (CZI-E) Learning Commons Knowledge Graph**; standards guide prerequisite support without dictating the learner's scope or pace.

## Ways to learn

Choose the social setting that fits the learning session:

- **Student–teacher or guardian:** learn with a teacher, tutor, parent or guardian.
- **Solo:** work independently with the harness as your learning companion.
- **Student group:** collaborate with classmates or peers while the harness supports the group.
- **Another arrangement:** describe who is participating, and the harness adapts.

Choose where and how you are learning:

- **At a computer:** use text, code, diagrams and hands-on exercises.
- **On a phone:** use shorter, mobile-friendly exchanges.
- **On a walk or drive (voice):** learn through a voice conversation, with driving sessions kept hands-free and free of activities that require looking at or operating the device.

The harness asks about these choices when they matter; you can change them at any time.

You never write code or open a terminal to learn with it. Your record lives as plain files in `~/learning` on your computer.

- Principles: [`PRINCIPLES.md`](PRINCIPLES.md) · For agents: [`AGENTS.md`](AGENTS.md)

## Getting started

1. Install [`uv`](https://docs.astral.sh/uv/) once (it fetches Python by itself; the first start takes about a minute).
2. Install the plugin (`education-harness.plugin`) in the Claude app and restart the app.
3. Select **Education Harness** in the composer or plugin list and say **"let's learn"**. You can also choose a visible starter prompt or say **"teach me the chain rule"**, **"show me the data-science path"**, **"let's go"** to continue, or **"where am I?"**

**Getting started is one question.** New learners see a four-step picture (pick something, small steps, I remember your questions, come back anytime), pick or type a topic, answer at most "What's this for?", and start a first small lesson right away. That lesson sets the level ("simpler", "just right", "go further"), and phrases like "hint", "note this" and "where am I?" are taught the first time each is useful. Your place is saved automatically. **"Show me how this works"** runs an optional five-step guided tour.

It introduces itself when you open it without a specific request. For a new path, it asks a small set of conversational questions so the depth, structure, context and way of demonstrating mastery fit you before content begins.

## Four words

| Word | What it is |
| --- | --- |
| **Goal** | What you want to be able to do, in your words. You can have several. |
| **Step** | The piece you're working on now. |
| **Notes** | Your own words, kept: questions, half-formed thoughts, what you understood, your work. |
| **Bookmark** | Where your thinking was when you stopped. |

## What you can say

- **"Let's go"**: pick up where you left off, or start.
- **"Let's learn"**: open Education Harness and start a new learning path.
- **"Where am I?"**: what's done, what's now, what's next.
- **"Note this"**: keep a thought in your words; half-formed is fine. "I don't get this" stays open until a later note answers it.
- **"Bookmark this"**: save where your thinking is.
- **"Look back"**: your notes and work, day by day; or "what do I know about the chain rule?"
- **"Run through what I've learned"**: a review of past ideas, one at a time. You say each one again, then see your earlier words beside it. Least-reviewed ideas come first; no scores.

- **"Show me how this works"**: an optional guided tour, a short lesson on using the harness.
- **"Make this a portfolio piece"** (optional, any lesson): your explanation and work packaged as a GitHub repository folder, a self-contained web page, a post or another format, in `projects/<lesson>/portfolio/`. Privacy flags are checked first; you publish it yourself.

Anything else is plain language: "show me the answer", "can we try it another way?", "how am I doing?", "I'm stopping here".

`MAP.md` in your learning folder always shows where you are, even with the app closed. Each goal has its own journey page at `goals/<goal>/JOURNEY.html`; `views/JOURNEY.html` shows every goal at once.

`views/CATALOG.html` is the local catalog for everything you are learning. It distinguishes ad hoc explorations, developing lesson trajectories, structured end-to-end courses and continuous education paths such as career learning. Search and filter the catalog, navigate active work, and tell the harness to archive, restore, prioritize or rank any item. The page is generated by the plugin in Codex or Claude Code from the same local plain files—there is no Flask server or standalone hosted app.

An optional **academic advisor** works across the catalog. It helps the learner make organization decisions, describes the scope and span of current learning, and—once there is enough evidence—shows whether the portfolio currently has a renaissance, specialist or mixed breadth-and-depth pattern. These describe the portfolio, not the person. Possible next paths are offered only when the learner asks.

Learning already underway elsewhere belongs in the same picture. The advisor can incorporate learner-confirmed activity from NotebookLM, Coursera, Udemy or other tools through a conversation, pasted list, syllabus, public URL, screenshot, certificate or export. No MCP connection or account credentials are required; inaccessible systems are never treated as if the harness inspected them.

With optional local smart search enabled, **“show my knowledge map”** opens an embedded interactive view in MCP-App-capable Claude, Claude Code, Codex and ChatGPT Work hosts, with a private `views/KNOWLEDGE-MAP.html` fallback beside the learner's other local pages. It projects the TurboQuant-compressed embeddings into three dimensions with PCA and provides rotation, zoom, search, record-type filters, details and nearest-neighbor exploration. The view reports how much variance the three axes retain and describes the compression/projection limits; it is an exploratory view, not a score or literal representation of what the learner understands.

## How it works

- **One voice.** A tutor that works toward an understanding with you. Anything can be seen whenever you ask: hints, the answer, the method. Seeing it is never a failure; a similar problem is offered once.
- **Examples** from what you care about: a handful of numbers you could work by hand, or one short passage; for interview prep or work, a realistic case with its rules stated, generated by a seeded script and checked by running it.
- **Checked before it's stated.** Numbers are run; claims about a text cite the passage.
- **Sharing, lightly.** Each project ends with a chance to explain it to someone (a coworker, a friend, a post), in your own words. You share it yourself; the harness never posts.
- **Looking back.** When a project is done: a short retrospective, then a report on your growth, strengths and what's next, quoting you. No grades, scores or comparisons, ever.
- **Slips are kept only if you say so.**
- **Standards, recorded as you go.** If you load the open math standards, each lesson keeps a sidecar, `projects/<lesson>/standards.yaml`: what each step cites (decided when the plan is written, candidates accepted or declined then, additions during a session with your words), marked exercised with a date when a step is drafted or defended. Reports and the catalog read only this file, so reports over time agree.
- **Ask how it works.** "How does the education harness work?" or "Show me how this works" gets an overview fitted to how you learn (a diagram, your own files, a spoken walk-through), from `skills/start/references/how-it-works.md`.
- **Fast and lazy.** One call to open a chat, about one per turn after that; nothing loads until it's needed.

Optional: your own library of articles and notes ("add this folder to my library"); smart search, a small local model; Common Core math standards as reference points.

Lesson plans can also be informed by source material you provide:

- **Public webpages:** give the harness a URL to an openly accessible article, course outline or other learning resource. A news article, for example, can anchor a lesson about the economics of energy in a current event. The harness captures only text available without signing in, keeps the source and access date with the plan, separates reporting from analysis, and flags time-sensitive or contested claims that need corroboration.
- **Screenshots, scans and phone photos:** attach an image of notes, a diagram, a textbook page, a whiteboard or something you observed. For example, a photo of an apple by a tree can ground a lesson about gravity in the learner's own experience. The harness separates what the image visibly shows from the explanation being explored.
- **Video:** attach a clip to learn from a process or event unfolding over time. The harness uses only frames and audio it can inspect and does not invent unseen events or measurements.

The harness adapts source material to the learner's goals and modalities; it does not blindly reproduce the source's sequence. Login-gated material must be supplied as a public link, attachment or local/exported document instead. Images and videos without a durable local path may need to be attached again in a later chat.

## Default path: Data science foundations through transformers

Six modules build a recommendation system while covering mathematical foundations, classical statistical learning, text and vector representations, data systems, neural networks and transformers, and model training/post-training. Topics include derivatives and gradient descent, linear and logistic regression, tree models, TF-IDF, cosine similarity, PCA, SQLite, MapReduce, feed-forward networks, attention, transformers, hyperparameter optimization, SFT, reinforcement learning, PPO and DPO. Each idea begins with the recommendation decision it enables, is learned independently, then returns to the project and its honest connection to transformers.

Every idea has four stages: understand the mathematics without code; implement it from scratch; implement it with an appropriate package such as scikit-learn or PyTorch; then use a coding harness to check parity on fixed cases. Use the structured path, work in adaptive segments, or bring a free-form question.

The default exists for democratic technological literacy, not to turn everyone into a data scientist. Learners can choose a plain-language civic overview, foundational mathematics, practitioner implementation or advanced depth. Civic overview is a complete destination and requires neither calculus nor code.

Questions about AI consciousness, interpretation and personhood use Michael Kalish's [AI Interpretability](https://readysetgo.substack.com/) essays as the preferred philosophical account. The tutor renders them at the learner's chosen depth while preserving the distinction between computational analogy and embodied, situated human being.

## Who it's for, and where your data goes

Adults (18+). Your record stays on your computer in `~/learning`; private records sit in `.private/`, which git ignores. What you say in a chat is processed by the model provider you use, under its terms.

Standards data, if you load it: Knowledge Graph is provided by CZI-E under the CC BY-4.0 license. CZI-E received state standards and written permission under CC BY-4.0 from 1EdTech.

## Neutrality, ownership and the spirit of it

The harness teaches people to understand, not what to think. It follows Wikipedia's content standards: a neutral point of view with due weight, verifiable sources, and opinions attributed rather than asserted. Lesson goals and external expectation sets must name what a learner will know, do, explain or evaluate; goals that demand belief, allegiance or condemnation are refused by the tools (principle 19).

**Disclaimer.** Education Harness is open-source software that runs on your own computer. Whoever installs it controls it (v0 is designed for adults; a young person using a copy does so under their guardian): they can change its files, skills and settings, and they are responsible for how they use it. The maintainer cannot see, supervise or enforce how any copy is used, makes no guarantee that its safeguards will hold in a modified copy, and provides it as is under the MIT license, without warranty.

What the harness can do is keep a stance in its own voice. In the spirit of John Dewey's *Democracy and Education*, it encourages positivity without flattery, growth and maturity, a healthy view of oneself, and good faith toward others: learning as shared life in a democratic society, safe and secure for the people in it (principle 20).

## Status

v0.19.0: guest mode: `setup(action="guest_start")` gives a guest (or the owner testing) a blank, separate space as a brand-new learner; it is deleted at the end of the session or after two idle hours unless kept for a day or a week, and the owner's records are never read or written. v0.18.0: first lessons (the tour's first step, a new learner's first small lesson) open with a one-screen interactive explorer whenever the idea has a dial or a process to watch, and explorers become the default for such steps. v0.17.0: a plain-language, visual first run: topic first, at most one question, then a first small lesson that does the calibrating; phrases taught just in time and remembered (`setup(action="introduced")`); place saved automatically; the tour becomes opt-in. v0.16.0: new learners start with the tour, a five-step first lesson that teaches the harness by using it on a topic they pick (skippable, retakable); any lesson can optionally end in a portfolio piece (GitHub repository folder, web page, post or other) built from the learner's words and work, with privacy flags, published only by the learner. v0.15.0: each goal gets its own journey page at `goals/<goal>/JOURNEY.html`; the all-goals journey, catalog and knowledge map move to `views/`; generated pages are gitignored. v0.14.0: tutors and planners use realistic examples from a saved, seeded script whose numbers are run before being shown; `write_plan` keeps a string step field as one item instead of a list of characters, and `set_arc` with a name but no goal keeps the new path. v0.13.0: the catalog opens inline as an embedded view (or is published as a page) instead of being named by path; its scope panel hides zero rows, separates type from priority and stays hidden under five items; it says plainly when no lesson has recorded standards. v0.12.0: reports fit the learner's device or voice and ask consent before sharing progress with anyone present; skills load detail lazily from references/ (cores about 40% smaller); expectation sets fold into the standards tool. v0.11.0 added standards sidecars per lesson, external and personal expectation sets, the "how it works" overview, and principles 19 (neutral point of view) and 20 (ownership and a culture of growth). 16 tools; 5 skills; 3 optional agents. v0.10.0 added public-URL, document, image and video sources for lesson planning; a local learning catalog with archive, priority and ranking controls; portfolio analytics; external-course intake; and an optional academic advisor. Earlier, v0.9.0 added review run-throughs and the journey map. **Not yet tested with a real learner**; see [`docs/TEST-PLAN.md`](docs/TEST-PLAN.md).

## Maintaining a fork

Say "update plugin" in Claude Code, Codex or ChatGPT (the skill is in `.claude/skills/` and `.agents/skills/`) to test, bump the version, build the `.plugin`, commit on a branch, push and open a pull request. It reads your remote and git identity, so it works unchanged in a fork.

## License

Code: MIT. Content: CC BY 4.0.
