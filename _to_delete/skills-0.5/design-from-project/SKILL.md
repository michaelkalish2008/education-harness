---
name: design-from-project
description: Education harness lesson planner. Use to turn an arc item, a default-program idea or a learner's own question into a project plan of small steps with a tiny example from the learner's interests, and to write each step's hints, solution and follow-on problems. Also for accepted changes (a detour, a remedial step, a reorder). Runs as the lesson-planner subagent when one is available, so the tutor never sees solutions before they are revealed.
---

# Design from project: plans and solutions

Principles: 0, 1, 2, 3, 7, 8, 10.

## Inputs

- The arc item (`get_arc`), and the program idea if it has one (`get_program`).
- The learner's interests and formats (from the brief the caller gives you, or `where_am_i`).
- The audience (`get_share(project)`, or from the brief): who the learner will show this to, and the format.
- For a change: the accepted proposal, and the current plan (`get_plan`) and progress (`get_progress`).

## Build the plan

1. **The project question** comes from the learner's life: "Does a longer brew taste more bitter?", not "Learn linear regression".
2. **A tiny example**, shaped by the arc's lens (`get_arc` → `lens_detail.examples`): for math, 5 to 20 numbers or a handful of words or vectors, workable by hand (`example_hint` says what shape); for philosophy, one short passage, two sentences to compare, or a toy model of the concept; otherwise something small enough to hold in mind at once. Always from their interests. Invent plausible numbers only if they have none, and say so in the plan.
3. **Steps, built backward** from a working answer to the question: each step produces a working piece of it. Three to six steps per project. Each step:
   - `id` (s1, s2, …), `does` (one plain sentence a learner would understand), `concepts` (the program's concept ids where they fit),
   - `strong_version_shows` (two or three things a strong version shows),
   - `requires` (earlier steps), `format` (`solve-it` or `work-backward`),
   - `standards_cited` only where a code describes what the step teaches (reference only).
4. **Depth is the learner's choice** (principle 3): by hand, with numpy, or with a library; note which in `does`.
5. **The last step is the share-out:** `format: "share-out"`, `does` naming the audience and format ("explain to my team in a one-page explainer what SFT changed"), concepts the project's main ones, `strong_version_shows` e.g. [in my own words, one number that matters, one limit]. Earlier steps can mention the audience where it helps ("pick the example your team would recognize"), since preparing to teach helps learning. No solution is written for the share-out step.
6. **Constellation:** one question per domain (literature, history, ethics, law, sociology, philosophy) tied to the project. No readings unless read and checked.
7. Save with `write_plan(project, question, steps, example, interests_used, idea, constellation)`. Project names are short slugs from the question.

## Write the solutions

For every step except the share-out, `write_solution(project, step, hints, answer, method, follow_ons)`:
- Two or three hints, each smaller than the last reveal.
- The answer, and the worked method.
- At least two follow-on problems: siblings of the step with different numbers or a twist, each with its solution.
- **Apply the lens's checks** (`lens_detail.checks`): for math, run every number with code before writing it; for philosophy, cite the passage for every claim about a text and keep text and interpretation apart, quoting briefly and linking for the rest. If you can't check something, mark it unchecked (principle 7).
- Everything original (principle 8).

## Return to the caller

Only the project name, the question, the example and the step list in plain words. Never the hints, answers, methods or follow-ons: the tutor must not see them before the learner asks.
