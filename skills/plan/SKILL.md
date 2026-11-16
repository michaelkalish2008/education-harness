---
name: plan
description: Education harness planning. Use to turn what the learner wants to learn (a goal, an idea from the data-science path, or their own question) into a short project plan, and to change a plan they've asked to change.
---

# Plan

Plans are built backward from the learner's question, never from a syllabus. Keep it small and quick. Principles: 0, 2, 3, 7, 8, 19.

0. **Capabilities, not creeds (19).** Steps name what the learner will know, do, explain or evaluate; contested topics get due weight from reliable sources; decline plans built to persuade and offer the neutral version.
1. **Honor the lesson mode.** Read the accepted profile choice. For `structured`, create the complete three-to-five-step plan before teaching. For `semi-structured`, plan only the next coherent segment (one or two steps), then revise from the learner's direction without discarding worked steps. For `free-form`, do not impose a project plan: follow the current question and create a plan only if the learner asks for one or their question naturally becomes a project.
2. **Honor sociability.** `group` plans include roles or a shared task; `guided` plans identify what the tutor, teacher or parent does without doing the learner's work; `solo` plans keep every activity independently workable. Never assume other people are available merely because a share-out exists.
3. **Honor mastery modality.** For `written-practical`, `strong_version_shows` names a written explanation plus observable work (calculation, code, query, artifact or parity report). For `spoken`, it names an oral teach-back and responsive explanation; record the learner's words as their attempt, but do not force a written artifact. For `both`, use complementary written/practical work and spoken explanation before calling the learner's own work drafted. A formal defense remains optional in every mode.
4. **Honor depth as a destination.** Use `program.depth_modes`. Civic overview uses concrete decisions and critical questions with no calculus or code owed. Foundational uses small mathematical examples with optional code. Practitioner completes all four stages. Advanced adds derivations, assumptions, failure modes and extensions. Reduce module count as well as within-module detail. Never treat civic understanding as failed professional training.
5. **Honor learning context without narrowing education to a credential.** Interview plans include explanation and implementation practice relevant to the target role. School plans fit vocabulary, prerequisites and evidence to the stated level without teaching to a score. Curiosity/personal-growth plans follow the learner's questions. Professional-growth plans connect to the stated role and responsibilities.
6. **Calibrate before content.** The learner has stated what they want to do, and the tutor has checked the smallest relevant background/notation assumptions.
7. **Check prerequisite references.** Inspect `where_am_i`'s `standards.matches`; cite only genuinely relevant statements in `standards_cited`. Standards describe a step but never set scope.
8. **The question** comes from their life or words. For the data-science path, use the idea's `example_hint`.
   - A URL, document, screenshot, photo or video as source: read `references/sources.md` before planning (a syllabus or other expectations they want tracked goes to `../start/references/expectations.md` instead).
   - On the default data-science path: read `references/data-science-planning.md`.
9. **The example** (read `../tutor/references/examples.md`): for interview or professional growth, realistic scale and mechanism, posed as an interviewer would (a by-hand miniature only as a labeled stepping stone); otherwise tiny and from their interests. Write its generating rules into `example` and say whether they are stipulated or a noisy sample. Its numbers come from a seeded script or closed form, run before shown and saved with the lesson.
10. **Plan size:** structured uses three to five steps; semi-structured uses one or two. Each step is `{id, does, concepts, strong_version_shows, requires, terms?, standards_cited?}`.
    - `terms`: each word the step uses that has an everyday meaning, with the one meaning it has here as a concrete phrase, e.g. `{"average": "the average score over all views, with a click scored 1 and a non-click 0 (1 click in 10 views is 0.1)"}`. Pick one word per idea and don't reuse a word for a second thing.
11. **Explorers:** for a step whose idea turns on a quantity the learner can vary, name the explorer in `strong_version_shows` (what to vary, what to watch), so the tutor builds it at the start of the step.
12. **Share-out:** the final structured step is a share-out. Semi-structured adds one only when useful.
13. `write_plan(project, question, steps, example, audience, sources?)` when the chosen mode calls for a plan. It writes the lesson's standards sidecar and returns `standards.candidates_to_review` once: read each statement and `standards(action="review", code, decision)` with the learner; accept only what a step will exercise. Reports use only this, so decide here.
14. **Solutions:** skip by default; work them out and check them on request.
15. Tell the learner the plan or current segment in two or three lines, then start below the first unconfirmed prerequisite.

For a goal with several parts, propose the path in plain words after the first session, from what they actually did, and save it with `set_arc` on their yes. Choose the lens that fits (math, philosophy, general) and say it in one line.
