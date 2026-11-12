---
name: retrospective
description: Education harness retrospective, a short look back in the learner's own words that feeds the retrospective report. Use when a project is finished (the help card suggests "let's look back on this project"), when the learner says "let's do a retro", "look back on this project", "what did I learn from this?", or at the end of a period they choose.
---

# Retrospective: looking back, in your own words

Dewey calls reflection the reconstruction of experience: going back over what happened so the next experience goes further. The retrospective is the learner's own; the report that follows is the mentor's reading of it. Principles: 0, 4, 5, 13, 18.

## Before asking

1. `journal(project=…)` for the whole project, and `get_share(project)`.
2. Open with two or three lines of what they did, in plain words and quoting them once, so they aren't answering from a blank page.

## Ask, one at a time (any can be skipped)

- **went_well:** What went well, or what are you glad you did?
- **was_hard:** What was hard?
- **surprised:** What surprised you?
- **differently:** What would you do differently next time?
- **how_i_learn:** What did you notice about how you learn best? (A format, a time of day, talking it through, drawing it.)
- **sharing:** Who did you show it to, and how did it land? If they didn't share it, offer the five-minute walkthrough once, lightly.
- **next:** What do you want to do next?

Keep their words. Don't correct, grade or reframe their answers. Reflect back briefly if it helps, then move on.

## After

1. `save_retrospective(answers, project)`.
2. If `how_i_learn` names a format that works, propose it as a profile change (`propose_profile_change`); they accept or edit.
3. If `next` suggests a change to the arc, offer it (**check-in**, part *Arc*).
4. Load the **report** skill for the retrospective report on this project.
