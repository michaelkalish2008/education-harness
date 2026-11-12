---
name: plan
description: Education harness planning. Use to turn what the learner wants to learn (a goal, an idea from the data-science path, or their own question) into a short project plan, and to change a plan they've asked to change.
---

# Plan

Plans are built backward from the learner's question, never from a syllabus. Keep it small and quick. Principles: 0, 2, 3, 7, 8.

1. **The question** from their life or their words: "Why does the chain rule multiply?", not "Learn derivatives". For the data-science path, use the idea's `example_hint` (see `where_am_i` `program`).
2. **A tiny example** by lens: math, 5 to 20 numbers or a handful of words or vectors, workable by hand; philosophy, one short passage or two sentences to compare; otherwise something small enough to hold in mind. From their interests when known.
3. **Three to five steps**, each `{id, does, concepts, strong_version_shows, requires}`. `does` in one plain sentence. Depth is their choice: by hand, NumPy or a library.
4. **Last step: share-out** (`format: "share-out"`), naming who they'd show it to. If the audience isn't known, write "someone you'd explain it to" and let the tutor ask later.
5. `write_plan(project, question, steps, example, audience)`. Project names are short slugs.
6. **Solutions:** skip by default; the tutor works them out and checks them on request. Pass `solutions` only where an answer needs computed numbers worth checking ahead of time, and run them first. If the **lesson-planner** agent is available and the learner wants answers kept out of sight, delegate this step to it.
7. Tell the learner the plan in two or three lines, then start the first step.

For a goal with several parts, propose the path in plain words after the first session, from what they actually did, and save it with `set_arc` on their yes. Choose the lens that fits (math, philosophy, general) and say it in one line.
