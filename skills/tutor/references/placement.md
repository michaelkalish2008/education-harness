# Placement: find where the learner stands before the first explanation

Read this whenever a topic is new to this learner: a cold chat, the tour's s1, a new learner's first small lesson, a new goal, or a step whose concepts they've never met. A profile (`depth_mode`, `formats_that_fit`) says how they like to learn, not what they know about this topic. A degree, a job title or a project name is not placement either. Placement costs one turn; teaching at the wrong rung costs the lesson.

## 1. Look before you ask (silent, one call)

`look_back(query=<topic in their words>)` across every goal. Notes, attempts and `keep` lines on related concepts are evidence of what they've used; a slip or open question is evidence of where it broke. Nothing found means cold, not beginner.

## 2. Draw the ladder (for yourself, never shown as a list)

Three to six rungs from the plainest idea the topic needs to the idea they asked for, each a thing they could *do*, in plain words. Every word you plan to use in the lesson sits on a rung, so a word with no rung is a word you haven't earned yet. Example, "does a disclaimer hurt the funnel?":

1. a rate: 400 of 1,000 reached checkout is 40%
2. comparing two rates: 40% vs 37% is a gap of 3 percentage points (not 3%)
3. a random split: why we flip a coin per user instead of comparing last week to this week
4. chance wobble: two groups with no real difference still land on different rates
5. group size and wobble: bigger groups wobble less
6. standard error, a z-score and a test

Check the ladder against `standards.matches` for quantitative material (the statement, not the code).

## 3. Ask one placement question, then teach

Before any explanation or explorer, ask one concrete question that sits in the middle of the ladder, answerable in a sentence, with **Not sure** and **Skip**. Make it something to do, not a self-rating: "Say a 40% and a 37% checkout rate. Is that gap big enough to act on? Say what you'd want to know." Not "How familiar are you with A/B tests?".

- Their answer uses the rung's idea correctly: start one rung above it, and name the next rung's new word before using it.
- Partly right, or right with the wrong word (a count read as a rate, percent for percentage points): start at that rung.
- Not sure or Skip: start at rung 1, in plain words. That's a placement, not a failure.
- They say "just teach me": start at rung 1, move fast, and let their answers move you up.

Say the placement back in one line, in their terms ("We'll start from how chance alone moves two rates apart, then build to the test"), and keep going in the same reply. Then save it once with `note(kind="keep", concept=<topic>, text="started at: <rung, in their words from the answer>")`, so the next cold chat finds it in step 1.

## 4. Keep placing while you teach

- **Every word on screen is earned.** An explorer, a table or a sentence uses only words already said in this chat, used by the learner, or defined on the screen next to them. Each control and number gets a one-line label of what it is and what moving it does. A derived quantity (standard error, gap ÷ SE, a log-odds) waits for its rung.
- **"I don't understand" is a placement signal.** Don't re-explain the whole thing at the same level. Ask which word lost them, or drop one rung and rebuild from there with one idea a turn.
- Work beats self-report in both directions: move up when they breeze through, down when they stall, and say so in one line.
