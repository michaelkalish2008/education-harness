---
name: review
description: Education harness run-through of past learnings. Use when the learner says "run through what I've learned", "review", "let's review", "quiz me on what I know", "practice my sentences", "warm me up", or wants to rehearse earlier concepts before an interview or a new step.
---

# Review

A run-through brings back what the learner already worked out, in their own words, and has them say it again. It is practice, never a test: no scores, no right/wrong tallies, no streaks. Principles: 1, 4, 5, 7, 18.

## Start

1. `look_back(kind="review")`, with `project` or `concept` if the learner named one, and `limit` if they gave a size ("three quick ones"). Default to about five cards.
2. One line: how many cards, and that the ones with the least attention come first. Don't list them.
3. If the deck is empty, say what becomes a card (anything kept with "remember this", insights, questions they later answered) and offer to start one now.

## Each card (one per turn)

1. **Prompt without the answer.** Name the concept and ask an open question that their saved words answer, e.g. "Standard error and views: how do they move together, and why?" In an interview context (`learner.learning_context`), ask it the way an interviewer would. Don't show their saved words yet.
2. **They say it.** Typed or spoken, rough is fine. In a voice session follow the tutor's *Voice sessions* rules: short, no symbols, no hypothetical numbers.
3. **Then show their earlier words** from the card (`your_words`, `insights`, `then_and_now`) next to what they just said. Ask what changed, or name one thing that's now sharper or one piece that dropped out. Never call the earlier version "the answer"; it's their own earlier wording, and either version can be the better one.
4. **Check before you state.** If either version has a factual or numeric error, say so plainly and fix it together (run the numbers). Don't let a review re-teach a slip into memory.
5. **Record it.** `note(kind="review", responds_to=<card id>, text=<what they said this time, in their words>)`. Their words go in as said; tighten only if they ask, and then save the tightened version as theirs only on their yes.
6. Move to the next card, or stop if they want.

## Shapes worth offering (once, when it fits)

- **Interview drill:** one card, three follow-ups an interviewer would ask.
- **Connect two:** pick two cards and ask how the ideas relate.
- **Explain to someone:** say it for a named audience (a teammate, a non-technical manager).
- **From the other side:** give a wrong claim and ask them to correct it.

## Ending

One line: how many cards they ran through and one thing that came out clearer, quoted. If a card exposed a gap, keep it as `note(kind="question")` on that concept so the tutor picks it up later. Then name the next step on their goal ("say 'let's go' to continue <step>").
