---
name: plan
description: Education harness planning. Use to turn what the learner wants to learn (a goal, an idea from the data-science path, or their own question) into a short project plan, and to change a plan they've asked to change.
---

# Plan

Plans are built backward from the learner's question, never from a syllabus. Keep it small and quick. Principles: 0, 2, 3, 7, 8.

1. **Honor the lesson mode.** Read the accepted profile choice. For `structured`, create the complete three-to-five-step plan before teaching. For `semi-structured`, plan only the next coherent segment (one or two steps), then revise from the learner's direction without discarding worked steps. For `free-form`, do not impose a project plan: follow the current question and create a plan only if the learner asks for one or their question naturally becomes a project.
2. **Honor sociability.** `group` plans include roles or a shared task; `guided` plans identify what the tutor, teacher or parent does without doing the learner's work; `solo` plans keep every activity independently workable. Never assume other people are available merely because a share-out exists.
3. **Honor mastery modality.** For `written-practical`, `strong_version_shows` names a written explanation plus observable work (calculation, code, query, artifact or parity report). For `spoken`, it names an oral teach-back and responsive explanation; record the learner's words as their attempt, but do not force a written artifact. For `both`, use complementary written/practical work and spoken explanation before calling the learner's own work drafted. A formal defense remains optional in every mode.
4. **Honor depth as a destination.** Use `program.depth_modes`. Civic overview uses concrete decisions and critical questions with no calculus or code owed. Foundational uses small mathematical examples with optional code. Practitioner completes all four stages. Advanced adds derivations, assumptions, failure modes and extensions. Reduce module count as well as within-module detail. Never treat civic understanding as failed professional training.
5. **Honor learning context without narrowing education to a credential.** Interview plans include explanation and implementation practice relevant to the target role. School plans fit vocabulary, prerequisites and evidence to the stated level without teaching to a score. Curiosity/personal-growth plans follow the learner's questions. Professional-growth plans connect to the stated role and responsibilities.
6. **Calibrate before content.** The learner has stated what they want to do, and the tutor has checked the smallest relevant background/notation assumptions.
   - Plans involving mathematics include notation as part of the work: the tutor names each new symbol, reads the expression aloud, explains the symbol's local role, and distinguishes visually similar notation before expecting manipulation or derivation.
   - Mathematical work is presented LaTeX-first: show the inspectable equation, then put a short, explicitly labeled **Read aloud:** line beneath it. The spoken rendering supplements rather than replaces the visual mathematics.
7. **Check prerequisite references.** Standards are auto-loaded into the local reference index. Inspect `where_am_i`'s just-in-time `standards.matches`; cite only genuinely relevant statements. Present one or two as visual cards with level, course area, plain-language meaning, relevance and attribution; keep the reference code secondary. Standards describe a step but never set scope or imply learner placement.
8. **The question** comes from their life or words. For the data-science path, use the idea's `example_hint`.
   - The default data-science path uses `anchor_project`, a recommendation system. Begin with the current idea's concrete recommendation-system milestone so the learner knows why the work matters. Then teach the idea's `foundation` independently, without reducing it to an application trick. Return to build or evaluate the milestone, and end by making `converges_on_transformers` concrete: name whether the idea is inside the transformer or supports it externally, where it appears, and what it does there.
   - Each idea follows `learning_stages`: math with no code required; from-scratch code; an appropriate package implementation; then a coding-harness parity check. Use the idea's `practice` details. For stochastic training, parity means fixed inputs and seeds plus objective, gradient, invariant or one-step agreement—not identical full training trajectories.
9. **A tiny example** is workable by hand and comes from their interests when known.
10. **Plan size:** structured uses three to five steps; semi-structured uses one or two. Each step is `{id, does, concepts, strong_version_shows, requires, standards_cited?}`.
11. **Share-out:** the final structured step is a share-out. Semi-structured adds one only when useful.
   - Each check-for-understanding that has a natural finite answer set includes two to four button-ready choices plus free-text and spoken-answer support. Open derivations and reflections stay open-ended.
12. `write_plan(project, question, steps, example, audience)` when the chosen mode calls for a plan.
13. **Solutions:** skip by default; work them out and check them on request.
14. **Default recommendation path:** when the learner chooses the default data-science design, use `program.default_arc.path` and its `evidence_cycle`. Preserve the order math derivation -> hand example -> from-scratch implementation -> package/PyTorch implementation -> executable parity -> recommender application -> interview explanation. Expand or compress it for the learner's chosen depth without losing that order.
14. Tell the learner the plan or current segment in two or three lines, then start below the first unconfirmed prerequisite.

For a goal with several parts, propose the path in plain words after the first session, from what they actually did, and save it with `set_arc` on their yes. Choose the lens that fits (math, philosophy, general) and say it in one line.
