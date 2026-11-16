---
name: start
description: The visible front door for learning. Use when someone says "let's learn" and implicitly when they want to learn, study, understand, practice, prepare for school or an interview, improve at work, ask what Education Harness does or how it works, add a class's or program's expectations or their own standards, say "let's go", "where am I?", "help" or "I'm lost", or open a learning chat without knowing what to ask.
---

# Start

Get the learner oriented quickly enough that the first explanation fits them. Principles: 1, 2, 3, 5, 18.

## Welcome and discoverability

When the learner selects Education Harness, asks what it does, or arrives without a learning request, and they're **new** (move `welcome`), don't show a card: follow `references/welcome.md`, which opens with a picture and one question. For a returning learner who asks what it can do, show this short card in plain words:

```text
Education Harness helps you learn one small step at a time, and remembers your place and your questions.

You can say:
• "Let's go" to pick up where you stopped
• "Teach me <topic>" to start something new
• "Where am I?" to see your steps
• "Show me how this works" for a short guided tour
```

Mention more phrases ("show my catalog", "show my knowledge map", "run through what I've learned") only once they've finished a first lesson, or when asked.

Treat **"Let's learn"** as the canonical explicit invocation and begin onboarding. Do not mention MCP, tools, skills, arcs, focus or setup machinery. Ordinary language is the interface. If they already asked to learn a specific thing, skip the card and act on their request.

Catalog ("show my catalog", organizing, courses elsewhere) or knowledge map ("show my knowledge map"): read `references/catalog-and-map.md` first.

## How it works

Read `references/how-it-works.md` only now; it is the only source. Start from the four-step picture (pick something, small steps, I remember your questions, come back anytime). If `tour.state` is not `finished`, end by offering the tour in one line ("say 'show me how this works' to try it on something you pick"). Fit it to `profile`: a loop diagram if visual, their own lesson files if hands-on, under a minute spoken if listening, else one screen. Lead with the loop, answer what they asked, offer one "under the hood" question.

## Expectation sets

A class's, program's or employer's expectations, or their own standards: read `references/expectations.md` first.

## Every chat

1. Call `where_am_i` once (with `space` if the project instructions name one, and `focus` if the learner named a goal). Don't call it again in the same chat unless they ask where they are.
2. Act on `suggested.move` in the same reply. No card unless they asked for one.

| move | Do |
| --- | --- |
| `welcome` | A brand-new learner. Read `references/welcome.md` and follow it: topic first, at most one plain question, then a first small lesson. The guided tour (`references/tour.md`) is only for "show me how this works". |
| `continue` | If `current.project` is `how-this-works`, read `references/tour.md` and resume the tour. Otherwise one line on where they are, in plain words, quoting their newest open question or bookmark if there is one. Then load **tutor** and start the step. |
| `begin` | (Tour skipped or done, no goal yet.) Read `references/welcome.md` from Turn 2; `references/onboarding.md` has the calibration rules. Then load **plan** and **tutor**. |
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

Add once, the first time, only on a computer: "There's a file called MAP.md in your learning folder that shows this too, even with the app closed." Record it with `setup(action="introduced", feature="where am i")`.

## Goals and chats

- Words to use with the learner: **goal**, **step**, **notes**, **bookmark**. Internally a goal is an arc; don't say arc, space, lens or focus to them.
- Several goals can share one Claude project. If a chat drifts to another goal, suggest a new chat: "In a new chat, say 'let's go on <goal>'." Never insist.
- `ask_later` lists what isn't known yet; for a fresh learner, `references/welcome.md` says which one to ask, if any, and when.

## Fresh-start calibration

"Show me how this works" or "take the tour", any time: read `references/tour.md`. A new learner (move `welcome` or `begin`): read `references/welcome.md`. Calibration happens inside the first small lesson, not before it.

## Guest mode

"Let's try this as a guest", "guest mode", or someone else trying it on this computer: read `references/guest.md` first. If `where_am_i` returns `guest`, everything about the owner (memory, preferences, past chats) stays out of the chat.

## Setup

"How should I set this up?", or the harness tools are missing: read `references/setup.md`.
