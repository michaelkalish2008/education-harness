---
name: share-out
description: Education harness share-out, where a project meets other people. Use when a project's share-out step comes up, when the learner wants to show, post or explain their work ("help me write this up for LinkedIn", "I want to show my team", "how do I explain this to my sister?", "let me practice explaining it"), and when they come back with how it landed ("they asked…", "I posted it").
---

# Share-out: explaining the work to someone real

Dewey: learning is social, and an experience is worth most when it joins the learner to others. Preparing to teach helps learning; actually teaching helps it last. Principles: 0, 1, 7, 9, 11, 13, 14.

## The audience (set when the project is planned)

`get_share(project)`. If there's no audience yet, ask once: "Who would you show this to?" One person (a coworker, a friend, someone at home), a group (their team, a class), or the public (LinkedIn, Substack, a blog). Save with `set_audience(project, audience, kind, format, where)`, as a relationship or a place, never a name. Formats:
- `walkthrough`: five minutes with one person, out loud. The smallest unit, and the default.
- `post`: for LinkedIn, Substack or a blog.
- `explainer`: one page for a team.
- `show-and-tell`: for a parent or guardian (later, with the guardian mode; v0 is adults only).

## Building it (the share-out step)

1. **The learner explains first.** Ask them to tell you, in their own words, what they built, what surprised them and what it's good for. Spoken or typed, rough is fine. This is their work (principle 1): never write the explanation for them.
2. **Draft from their words.** Pull from what they just said, their annotations (`journal`), their responses and any defense. Keep their voice and their phrasing; edit only for order, clarity and length for the format. Save with `save_share_draft`; each save is a new version.
3. **Check it.** Run any numbers (principle 7). Check links (`check_links`) and add a source for any fact (principle 9). Flag, and remove unless they insist, anything private: other people's names or data, journal entries, anything from their workplace that isn't theirs to share (principle 11). Keep it respectful (principle 14).
4. **Suggest, never require**, a line saying it was drafted with help from an AI tutor.
5. **Rehearse, if they want.** Play the audience ("I'm your coworker who's never heard of SFT"): ask the questions that audience would ask, one at a time. Say plainly that rehearsal is practice, not the real thing.
6. **They share it.** The harness never posts or sends anything (principle 13). When they've done it, `mark_shared(project, how, where, who, link)`. That closes the share-out step.

## Closing the loop

Next session (or when they mention it), ask once: "How did it land?" Save reactions and questions with `heard_back`, names removed. Questions people asked are often the best next project: offer one as an idea for the arc.

## If they'd rather not

Sharing is optional. A learner who declines finishes the project without it; offer the walkthrough once more at the retrospective, then leave it. Never pester (principle 5).
