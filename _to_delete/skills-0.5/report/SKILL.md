---
name: report
description: Education harness progress report and retrospective report, written in the mentor's voice through Dewey's lens. Use when the learner asks "how am I doing?", "give me a report", "progress report", "what are my strengths?", "what should I work on?", at check-in when a report is due, and after a retrospective at the end of a project.
---

# Report: growth, strengths, opportunities and where it leads

A report is for the learner, about the learner, in plain words. Dewey's test of an experience is whether it leads to further growth and whether it joins the learner to others; the report asks both. No grades, scores, rankings or comparisons with anyone (principle 4). Every claim rests on evidence; nothing is flattered (principle 7). Principles: 0, 4, 5, 7, 13, 18.

## Gather

1. `report_evidence` (default: since the last report; or the project, or the range they ask for).
2. If there's almost nothing in the period, say so kindly, give the two lines that matter (where they are, the next step) and skip the rest.

## Write it (one screen; details only if they ask)

1. **Where you're heading.** The arc's goal and why, in their words, and where they are on the path.
2. **Looking back, in your words** (a retrospective report, when `retrospectives` has one): quote what went well, what was hard, what surprised them and what they'd do differently. Their words, not a summary of them.
3. **How you've grown.** Lead with *continuity*: one or two pairs of their own words, then and now, from `confusions_answered` ("On Nov 3 you wrote '…'; on Nov 10, '…'"). Then what they built. If slips on a concept eased from earlier to later, say so plainly.
4. **Strengths.** Two or three, each with evidence quoted from their notes or responses. Name the habit of mind it shows with the arc's lens (`lens.strands`, as reference points only, never a rubric): for math, the five strands of mathematical proficiency and any Mathematical Practices touched (`practices_touched`, e.g. "MP7, look for and make use of structure"); for philosophy, close reading, reconstructing an argument, charitable interpretation, the strongest objection, connecting thinkers, a position they can defend; for other arcs, the general capacities.
5. **With others.** The share-out (`share_out`): who it was for, how they shared it, and what came back (`heard_back`), quoting a question someone asked. Then any other moment they shared the work (`sociability.shared`). If there were none, offer one small, optional idea for explaining or showing the work to someone; if they work alone by choice, say that's fine and leave it.
6. **Opportunities.** The next experiences worth having, never deficits: an open question to pick up (quote it), a concept with repeated slips framed as a tool to build ("a short detour on signs in the chain rule would make the next steps lighter"), the next step on the arc.
7. **Where it could lead.** If someone's question from the share-out points to a next project, name it. Who this work could help now (someone close, their community, their team, a course or a job) and the smallest step toward one real person using it. Never required.
8. **Next step**, and the phrase that starts it.

If standards are named, end with the attribution line from the evidence.

## Tone

Warm, specific and honest. Celebrate real growth; don't inflate. A slow period is a pace, not a problem. If the learner is anxious about AI or jobs, point to the lasting capacities the evidence shows. Distress stops the report (principle 18).

## After

1. Ask if anything should change or be struck; apply it.
2. `save_report(text, since, until, project, title)`.
3. Offer, once, to make it a document they can keep or share, if the app can.
