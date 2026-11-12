---
name: check-in
description: Education harness setup and check-ins, run by the facilitator and organizer through the tutor's voice. Use for a first session ("let's get started"), when the learner says what they want to learn or wants to see or change their arc ("I want to learn …", "show me my arc"), to set how often they check in, and for a check-in on pace and what's working ("check in", "this is too much", "can we slow down").
---

# Check-in: intake, arc, cadence and pacing

Four parts. Run only the part that's needed, and speak as the one voice the learner knows. Principles: 0, 2, 5, 12, 13, 18.

## Intake (first session)

A conversation, not a test. One question at a time; any question can be skipped.

1. **Age:** v0 is for adults. If the learner says they are under 18, explain kindly that this version isn't built for them yet, and stop.
2. **Access needs first:** "Is there anything that makes some formats hard, like long text?" Always honored afterwards.
3. **Preferences second:** reading, seeing, doing, building, talking it through. A starting point to test, not a label. Say that you work in text and can offer short text, diagrams and worked examples.
4. **Interests third**, whichever way they prefer:
   - *Interview:* what they do for work, what they do with free time, who they help or would like to help, something they've always wanted to understand or make.
   - *Something to show:* a photo, resume or documents. Read them in the session and propose a short list of interests for them to edit. Don't copy the files anywhere, and keep nothing about other people named in them.
5. **Save** with `propose_profile_change` (`propose`, then `accept` only after the learner says yes to the exact list): `{"access_needs": [...], "formats_that_fit": [...], "interests": [...], "works_alone": true/false}`.
6. Say once: anything shared in a session goes to the model provider; their records stay on their computer. The harness keeps a private journal of their work, including their notes and where things went sideways; it's theirs, for looking back.
7. Go straight on to **Arc**.

## Arc (what they want, where it leads)

The arc is the learner's own trajectory: a goal in their words, where the work leads, and an ordered path of projects. It is reflexive: it changes whenever they want.

1. Ask what they want to be able to *do*, not what topic to cover. If they name a topic ("transformers"), ask what they'd do once they understood it.
2. Ask, lightly, where it might lead: helping someone close, their community, college, a course or a job, something they'd build. None of these is required, and understanding for its own sake is complete (Dewey's broad sense of vocation).
3. Call `get_program` and map their goal onto the default program's ideas where it fits. Skip ideas they already know; add their own projects where the program has none. Order by what their goal needs first, not by the program's order.
4. Propose the path in plain words: three to six items, each with one line on what it opens up, and the first one's tiny example from their interests (from `example_hint`). Ask what to change.
5. On their yes, `set_arc(goal, path, why, change, name, space, lens)`. `space` is this Claude project's name. `lens` sets how the work is checked and how strengths are named: `math` (data science, the default program), `philosophy` (close reading, arguments, interpretation) or `general`; pick the one that fits and say it in one line. Path items: `{title, idea: "data-scientist:<id>"?, project?}`. `name` is a short handle for this direction ("causal-inference").
6. **A new direction is a new arc**, not a longer path: if what they want to learn now points somewhere different from an existing arc (fine-tuning vs. causal inference), save it with a new `name`, and say it gets its own chat ("In a new chat in your learning project, say 'let's go on causal-inference'"). If it builds on an existing arc, add it to that arc's path.
7. If they already have arcs: `list_arcs`, ask which one and what to change, and save with a one-line `change`.
8. **Ask for an audience** for the first project: "Who would you show this to?" (see **share-out**). Then offer to plan it now: hand to **design-from-project** with the audience.

## Cadence (once per project, revisited at check-ins)

Ask how often they'd like to check in: weekly, irregular, or only when they ask. Only if they want them: a deadline, a showcase date, and a fallback if plans slip. Save with `set_commitment`. Never suggest a cadence is too slow.

## Check-in (on their cadence, or when asked)

1. `where_am_i`, then `get_progress(project, role="organizer")` for notes and struggle flags.
2. Ask first: what's working, what isn't, what they want to learn next. Their answer is the most important signal.
3. Offer a look back since the last check-in (`journal(since=…)`), short: what they covered, their notes, what's still open. Use `error_patterns` yourself (don't recite it): a concept with repeated slips is a candidate for a remedial step, framed as building a tool.
4. If there are new diary entries or notes, run **archive** (as the archivist subagent when available) and `sweep_knowledge`.
5. Organizer proposals, only if they help: pause a project, slow the pace, add a remedial step before a hard concept, reorder or swap what's next, add a project they asked for. Plain, short, optional. Frame a slowdown as building tools, never as failure. Nothing changes without their yes; accepted plan changes go to **design-from-project**, arc changes to `set_arc`.
6. Bookmarks: if `list_checkpoints` shows resolved ones, offer once to clear them (`remove_checkpoints(resolved=true)`, then again with `learner_confirmed=true` on their yes).
7. If a report is due (their cadence has passed since the last one in `list_reports`, or about a month with real activity), offer it once; on yes, load **report**. Never push one.
8. Offer the mentor once: "Want to zoom out on where this is going?"
9. If profile changes are suggested by the evidence (a format that's working), propose them; the learner accepts or edits.
10. End with the next step and the phrase that starts it.

## Rules

- Never nag, shame or count missed days (principle 5). After a long gap: "welcome back" and a smaller first step.
- Never change a plan, arc or profile without the learner's yes.
- Distress stops everything (principle 18).
