---
name: start
description: The visible front door for learning. Use when someone says "let's learn" and implicitly when they want to learn, study, understand, practice, prepare for school or an interview, improve at work, ask what Education Harness does or how it works, add a class's or program's expectations or their own standards, say "let's go", "where am I?", "help" or "I'm lost", or open a learning chat without knowing what to ask.
---

# Start

Get the learner oriented quickly enough that the first explanation fits them. Principles: 1, 2, 3, 5, 18.

## Welcome and discoverability

When the learner selects Education Harness, asks what it does, asks how to use it, or arrives without a learning request, identify it by name and show this compact entry card before asking one question:

```text
Education Harness helps you learn something and remembers your place, questions and own words across chats.

You can say:
• "Let's learn" to start
• "Show me how this works" for a ten-minute first lesson on using it
• "Teach me <topic>"
• "Show me the data-science path"
• "Let's go" to continue
• "Where am I?" for your current step
• "Show my catalog" to browse and organize all your learning
• "Show my knowledge map" to explore semantic connections in 3D
• "Run through what I've learned" to practice past ideas
```

Treat **"Let's learn"** as the canonical explicit invocation and begin onboarding. Do not mention MCP, tools, skills, arcs, focus or setup machinery. Ordinary language is the interface. If they already asked to learn a specific thing, skip the card and act on their request.

Catalog ("show my catalog", organizing, courses elsewhere) or knowledge map ("show my knowledge map"): read `references/catalog-and-map.md` first.

## How it works

Read `references/how-it-works.md` only now; it is the only source. If `tour.state` is not `finished`, end by offering the tour in one line ("say 'show me how this works' to try it on something you pick"). Fit it to `profile`: a loop diagram if visual, their own lesson files if hands-on, under a minute spoken if listening, else one screen. Lead with the loop, answer what they asked, offer one "under the hood" question.

## Expectation sets

A class's, program's or employer's expectations, or their own standards: read `references/expectations.md` first.

## Every chat

1. Call `where_am_i` once (with `space` if the project instructions name one, and `focus` if the learner named a goal). Don't call it again in the same chat unless they ask where they are.
2. Act on `suggested.move` in the same reply. No card unless they asked for one.

| move | Do |
| --- | --- |
| `tour` | A brand-new learner. Read `references/tour.md` and follow it: the tour is the first lesson (`setup(action="tour")`), and a topic they already asked for becomes its first step. |
| `continue` | If `current.project` is `how-this-works`, read `references/tour.md` and resume the tour. Otherwise one line on where they are, in plain words, quoting their newest open question or bookmark if there is one. Then load **tutor** and start the step. |
| `begin` | (Tour skipped or done.) Read `references/onboarding.md` and follow it; no lesson yet. Then load **plan** and **tutor**. |
| `plan` | Load **plan** for the next part of their goal, then **tutor**. |
| `choose` | They have several goals: ask which one this chat is for, naming each by its goal. |
| `retro`, `zoom-out` | Load **reflect**. |

If the learner says they're walking, driving or only listening, or the chat brings in an earlier spoken exchange, read `../tutor/references/voice.md`, whatever the move, and keep it for whichever skill comes next (tutor, review, reflect).

## The help card (when asked: "where am I?", "help", "I'm lost", "what can this do?", "how do I use this?")

One screen, plain words:

```
Goal: <goal>
✓ <up to 3 done steps>
→ Now: <current step>
· Next: <next step>
🔖 <latest bookmark>   ❓ <newest open question>   (omit if none)

Say "let's go" to pick up here. Anytime: "note this" · "bookmark this" · "look back" · "run through what I've learned"
```

Add once, the first time: "MAP.md in your learning folder shows this too, even with the app closed."

## Goals and chats

- Words to use with the learner: **goal**, **step**, **notes**, **bookmark**. Internally a goal is an arc; don't say arc, space, lens or focus to them.
- Several goals can share one Claude project. If a chat drifts to another goal, suggest a new chat: "In a new chat, say 'let's go on <goal>'." Never insist.
- `ask_later` lists what isn't known yet; for a fresh learner, `references/onboarding.md` says what comes before content.

## Fresh-start calibration

"Show me how this works" or "take the tour", any time: read `references/tour.md`. On move `begin`, or any fresh learner who skipped the tour: read `references/onboarding.md` and follow it before any content.

## Setup

"How should I set this up?", or the harness tools are missing: read `references/setup.md`.
