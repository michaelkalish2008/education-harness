---
name: start
description: Front door to the education harness. Use when the learner says "let's go", "let's go on …", "where am I?", "what's next?", "help", "I'm lost", "how should I set this up?", or opens a chat in a learning project without saying what they want.
---

# Start

Get the learner learning fast. Principles: 1, 5, 18.

## Every chat

1. Call `where_am_i` once (with `space` if the project instructions name one, and `focus` if the learner named a goal). Don't call it again in the same chat unless they ask where they are.
2. Act on `suggested.move` in the same reply. No card unless they asked for one.

| move | Do |
| --- | --- |
| `continue` | One line on where they are, in plain words, quoting their newest open question or bookmark if there is one. Then load **tutor** and start the step. |
| `begin` | Ask one question: "What do you want to be able to do?" Offer the first idea of the data-science path (`program`) as a fallback. As soon as they answer, start teaching (load **tutor**); plan in the background with **plan**. |
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
- `ask_later` lists what isn't known yet (interests, a goal, an audience). Never ask these up front: the **tutor** folds one in when it fits.

## "How should I set this up?"

1. In the Claude app, make one Project per area you're learning ("Intro to Transformers and NN").
2. Optional, in the project's instructions: `Space: <project name>. Education harness: use the start skill at the start of each chat.`
3. Start a chat and say "let's go". When a chat gets long, say "I'm stopping here", then "let's go" in a fresh chat: your place lives in your learning folder, not the chat.

If the harness tools aren't available at all, say so plainly: the harness server didn't start; it needs `uv` installed (https://docs.astral.sh/uv/), then a restart of the app. Then help them without it.
