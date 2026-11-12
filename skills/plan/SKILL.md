---
name: plan
description: Education harness planning. Use to turn what the learner wants to learn (a goal, an idea from the data-science path, or their own question) into a short project plan, and to change a plan they've asked to change.
---

# Plan

Plans are built backward from the learner's question, never from a syllabus. Keep it small and quick. Principles: 0, 2, 3, 7, 8.

1. **Honor the lesson mode.** Read the accepted profile choice. For `structured`, create the complete three-to-five-step plan before teaching. For `semi-structured`, plan only the next coherent segment (one or two steps), then revise from the learner's direction without discarding worked steps. For `free-form`, do not impose a project plan: follow the current question and create a plan only if the learner asks for one or their question naturally becomes a project.
2. **Honor sociability.** `group` plans include roles or a shared task; `guided` plans identify what the tutor, teacher or parent does without doing the learner's work; `solo` plans keep every activity independently workable. Never assume other people are available merely because a share-out exists.
3. **Calibrate before content.** The learner has stated what they want to be able to do, and the tutor has checked the smallest relevant set of background/notation assumptions. Do not turn a project title or a technically correct comment into evidence of fluency.
4. **Check prerequisite references.** Inspect `where_am_i`'s `standards.matches` when the topic is quantitative. Read the statements and cite only genuinely relevant prerequisites in `standards_cited`; an empty result or unloaded standards is explicit evidence that standards were not checked successfully, not permission to invent them. Standards describe the step but never set the project's scope.
5. **The question** from their life or their words: "Why does the chain rule multiply?", not "Learn derivatives". For the data-science path, use the idea's `example_hint` (see `where_am_i` `program`).
6. **A tiny example** by lens: math, 5 to 20 numbers or a handful of words or vectors, workable by hand; philosophy, one short passage or two sentences to compare; otherwise something small enough to hold in mind. From their interests when known.
7. **Plan size:** structured uses three to five steps; semi-structured uses one or two. Each step is `{id, does, concepts, strong_version_shows, requires, standards_cited?}`. `does` is one plain sentence. Depth is the learner's choice: by hand, NumPy or a library.
8. **Share-out:** the final structured step is a share-out. Semi-structured adds one only when that segment reaches something worth sharing. If the audience isn't known, write "someone you'd explain it to" and let the tutor ask later.
9. `write_plan(project, question, steps, example, audience)` when the chosen mode calls for a plan. Project names are short slugs.
10. **Solutions:** skip by default; the tutor works them out and checks them on request. Pass `solutions` only where an answer needs computed numbers worth checking ahead of time, and run them first. If the **lesson-planner** agent is available and the learner wants answers kept out of sight, delegate this step to it.
11. Tell the learner the plan or current segment in two or three lines, then start below the first unconfirmed prerequisite.

For a goal with several parts, propose the path in plain words after the first session, from what they actually did, and save it with `set_arc` on their yes. Choose the lens that fits (math, philosophy, general) and say it in one line.
