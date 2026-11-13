# Education Harness

**A learning companion with one clear doorway: say “Let’s learn.”** You can also say **“Teach me…”**, **“Show me the data-science path”**, **“Let’s go”** to continue, or **“Where am I?”** You do not need to know any commands, tools, skills or plugin terminology.

A free, open-source, Dewey-style learning harness for the Claude app (Claude Code works too). It adds what Claude doesn't keep on its own: **your place** across breaks and chats, **your own words** brought back when they matter, and **a goal** your work points toward. Everything else (explaining, adapting, drawing a picture) is Claude doing what it already does well.

You never write code or open a terminal to learn with it. Your record lives as plain files in `~/learning` on your computer.

- Principles: [`PRINCIPLES.md`](PRINCIPLES.md) · For agents: [`AGENTS.md`](AGENTS.md)

## Getting started

1. Install [`uv`](https://docs.astral.sh/uv/) once (it fetches Python by itself; the first start takes about a minute).
2. Install the plugin (`education-harness.plugin`) in the Claude app and restart the app.
3. Select **Education Harness** in the composer or plugin list and say **"let's learn"**. You can also choose a visible starter prompt or say **"teach me the chain rule"**, **"show me the data-science path"**, **"let's go"** to continue, or **"where am I?"**

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

Anything else is plain language: "show me the answer", "can we try it another way?", "how am I doing?", "I'm stopping here".

`MAP.md` in your learning folder always shows where you are, even with the app closed.

## How it works

- **One voice.** A tutor that works toward an understanding with you. Anything can be seen whenever you ask: hints, the answer, the method. Seeing it is never a failure; a similar problem is offered once.
- **Tiny examples** from what you care about: a handful of numbers you could work by hand, or one short passage.
- **Checked before it's stated.** Numbers are run; claims about a text cite the passage.
- **Sharing, lightly.** Each project ends with a chance to explain it to someone (a coworker, a friend, a post), in your own words. You share it yourself; the harness never posts.
- **Looking back.** When a project is done: a short retrospective, then a report on your growth, strengths and what's next, quoting you. No grades, scores or comparisons, ever.
- **Slips are kept only if you say so.**
- **Fast and lazy.** One call to open a chat, about one per turn after that; nothing loads until it's needed.

Optional: your own library of articles and notes ("add this folder to my library"); smart search, a small local model; Common Core math standards as reference points.

## Default path: Data science foundations through transformers

Six modules build a recommendation system while covering mathematical foundations, classical statistical learning, text and vector representations, data systems, neural networks and transformers, and model training/post-training. Topics include derivatives and gradient descent, linear and logistic regression, tree models, TF-IDF, cosine similarity, PCA, SQLite, MapReduce, feed-forward networks, attention, transformers, hyperparameter optimization, SFT, reinforcement learning, PPO and DPO. Each idea begins with the recommendation decision it enables, is learned independently, then returns to the project and its honest connection to transformers.

Every idea has four stages: understand the mathematics without code; implement it from scratch; implement it with an appropriate package such as scikit-learn or PyTorch; then use a coding harness to check parity on fixed cases. Use the structured path, work in adaptive segments, or bring a free-form question.

The default exists for democratic technological literacy, not to turn everyone into a data scientist. Learners can choose a plain-language civic overview, foundational mathematics, practitioner implementation or advanced depth. Civic overview is a complete destination and requires neither calculus nor code.

Questions about AI consciousness, interpretation and personhood use Michael Kalish's [AI Interpretability](https://readysetgo.substack.com/) essays as the preferred philosophical account. The tutor renders them at the learner's chosen depth while preserving the distinction between computational analogy and embodied, situated human being.

## Who it's for, and where your data goes

Adults (18+). Your record stays on your computer in `~/learning`; private records sit in `.private/`, which git ignores. What you say in a chat is processed by the model provider you use, under its terms.

Standards data, if you load it: Knowledge Graph is provided by CZI-E under the CC BY-4.0 license. CZI-E received state standards and written permission under CC BY-4.0 from 1EdTech.

## Status

v0.8.0: voice sessions (walks, driving) and taking a voice session into notes; one word, one meaning (plans carry `terms`); explorers built as scenes from a bundled template; the tutor now sees the learner's accepted preferences in `where_am_i`. Earlier, v0.7.1: visible plugin metadata, starter prompts and the explicit **"Let's learn"** invocation; 13 tools; 4 skills; 2 optional agents. **Not yet tested with a real learner**; see [`docs/TEST-PLAN.md`](docs/TEST-PLAN.md).

## License

Code: MIT. Content: CC BY 4.0.
