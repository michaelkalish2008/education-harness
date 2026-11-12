# Education Harness

A free, open-source, Dewey-style learning harness for the Claude app (Claude Code works too). It adds what Claude doesn't keep on its own: **your place** across breaks and chats, **your own words** brought back when they matter, and **a goal** your work points toward. Everything else (explaining, adapting, drawing a picture) is Claude doing what it already does well.

You never write code or open a terminal to learn with it. Your record lives as plain files in `~/learning` on your computer.

- Principles: [`PRINCIPLES.md`](PRINCIPLES.md) · For agents: [`AGENTS.md`](AGENTS.md)

## Getting started

1. Install [`uv`](https://docs.astral.sh/uv/) once (it fetches Python by itself; the first start takes about a minute).
2. Install the plugin (`education-harness.plugin`) in the Claude app and restart the app.
3. Make a Claude Project for what you're learning, start a chat, and say **"let's go"**, or just ask: "explain the chain rule".

It starts teaching right away. Anything it needs to know about you (what you're into, what you're heading toward, who you'd show the work to) it asks later, one question at a time, when it fits.

## Four words

| Word | What it is |
| --- | --- |
| **Goal** | What you want to be able to do, in your words. You can have several. |
| **Step** | The piece you're working on now. |
| **Notes** | Your own words, kept: questions, half-formed thoughts, what you understood, your work. |
| **Bookmark** | Where your thinking was when you stopped. |

## What you can say

- **"Let's go"**: pick up where you left off, or start.
- **"Where am I?"**: what's done, what's now, what's next.
- **"Note this"**: keep a thought in your words; half-formed is fine. "I don't get this" stays open until a later note answers it.
- **"Bookmark this"**: save where your thinking is.
- **"Look back"**: your notes and work, day by day; or "what do I know about the chain rule?"

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

## Default path: How to be a data scientist

Six ideas, from high-school math to a transformer small enough to trace by hand: a model is a function fitted to data; training is walking downhill on a loss; classification as a probability; meaning as direction (embeddings); a feed-forward network and backpropagation; a small transformer. Use it, skip around in it, or bring your own question.

## Who it's for, and where your data goes

Adults (18+). Your record stays on your computer in `~/learning`; private records sit in `.private/`, which git ignores. What you say in a chat is processed by the model provider you use, under its terms.

Standards data, if you load it: Knowledge Graph is provided by CZI-E under the CC BY-4.0 license. CZI-E received state standards and written permission under CC BY-4.0 from 1EdTech.

## Status

v0.6.0: 13 tools, 4 skills (start, tutor, plan, reflect), 2 optional agents (validator, lesson planner), 82 tests. **Not yet tested with a real learner**; see [`docs/TEST-PLAN.md`](docs/TEST-PLAN.md).

## License

Code: MIT. Content: CC BY 4.0.
