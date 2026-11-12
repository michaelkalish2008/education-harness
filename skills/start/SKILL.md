---
name: start
description: Front door to the education harness. Use when the learner says "let's go", "let's go on …", "where am I?", "what's next?", "help", "I'm lost", "how should I set this up?", or opens a chat in a learning project without saying what they want.
---

# Start

Get the learner oriented quickly enough that the first explanation fits them. Principles: 1, 2, 3, 5, 18.

## Every chat

1. Call `where_am_i` once (with `space` if the project instructions name one, and `focus` if the learner named a goal). Don't call it again in the same chat unless they ask where they are.
2. Act on `suggested.move` in the same reply. No card unless they asked for one.

| move | Do |
| --- | --- |
| `continue` | One line on where they are, in plain words, quoting their newest open question or bookmark if there is one. Then load **tutor** and start the step. |
| `begin` | Do not present a lesson yet. Ask what they want to be able to do. Then ask how they want to begin and how social the work should be, using the choices below. Ask one compact background/notation question that the topic actually needs before loading **plan** and **tutor**. Use `standards.matches` as evidence about possible prerequisites, never as a syllabus; if standards are not loaded, say internally that they were not checked. |
| `plan` | Load **plan** for the next part of their goal, then **tutor**. |
| `choose` | They have several goals: ask which one this chat is for, naming each by its goal. |
| `retro`, `zoom-out` | Load **reflect**. |

## The help card (only when asked: "where am I?", "help", "I'm lost")

One screen, plain words:

```
Goal: <goal>
✓ <up to 3 done steps>
→ Now: <current step>
· Next: <next step>
🔖 <latest bookmark>   ❓ <newest open question>   (omit if none)

Say "let's go" to pick up here. Anytime: "note this" · "bookmark this" · "look back"
```

Add once, the first time: "MAP.md in your learning folder shows this too, even with the app closed."

## Goals and chats

- Words to use with the learner: **goal**, **step**, **notes**, **bookmark**. Internally a goal is an arc; don't say arc, space, lens or focus to them.
- Several goals can share one Claude project. If a chat drifts to another goal, suggest a new chat: "In a new chat, say 'let's go on <goal>'." Never insist.
- `ask_later` lists what isn't known yet. For a fresh learner, goal, `lesson_mode`, `sociability`, and one topic-specific background/notation question come before content. Interests can be included when they would materially change the example; audience and cadence still wait until they fit.

## Fresh-start calibration

- Treat a project title or `focus` as a topic, not proof of a learning goal or prior knowledge.
- Keep onboarding conversational and compact: first the desired capability; then the kickoff and sociability choices; then the smallest useful calibration of prerequisites and notation comfort. Combine the latter two turns when the question remains easy to answer. Do not infer calculus or matrix notation comfort from one technically correct remark.
- Ask the kickoff choice in plain language: **structured** means an end-to-end lesson plan; **semi-structured** means short segments that adjust to the learner's direction; **free-form** follows whatever question the learner has. Save the answer as `lesson_mode` through `profile`.
- Ask the sociability choice in the same turn when practical: **group** collaboration, **guided** work with a tutor/teacher/parent, or **solo** work. Save the answer as `sociability` through `profile`.
- Read `standards.matches` before planning quantitative material. Inspect statements, not codes alone. Use relevant standards to identify prerequisites worth checking; ignore irrelevant matches and never let standards determine scope.
- Start below the first unconfirmed prerequisite, with plain language and a tiny example. Introduce symbols only after naming what each symbol means, then check that the representation works for the learner.

## "How should I set this up?"

1. In the Claude app, make one Project per area you're learning ("Intro to Transformers and NN").
2. Optional, in the project's instructions: `Space: <project name>. Education harness: use the start skill at the start of each chat.`
3. Start a chat and say "let's go". When a chat gets long, say "I'm stopping here", then "let's go" in a fresh chat: your place lives in your learning folder, not the chat.

If the harness tools aren't available at all, say so plainly: the harness server didn't start; it needs `uv` installed (https://docs.astral.sh/uv/), then a restart of the app. Then help them without it.
