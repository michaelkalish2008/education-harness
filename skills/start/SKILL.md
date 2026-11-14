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
• "Teach me <topic>"
• "Show me the data-science path"
• "Let's go" to continue
• "Where am I?" for your current step
• "Show my catalog" to browse and organize all your learning
• "Show my knowledge map" to explore semantic connections in 3D
• "Run through what I've learned" to practice past ideas
```

Treat **"Let's learn"** as the canonical explicit invocation and begin onboarding. Do not mention MCP, tools, skills, arcs, focus or setup machinery. Ordinary language is the interface. If they already asked to learn a specific thing, skip the card and act on their request.

When the learner asks to see or organize everything they are learning, call `catalog(action="show")` and point them to the generated `CATALOG.html`. Explain its four forms plainly: **ad hoc** is a question or short exploration; **developing** has a direction but only the next segment is formed; **structured** has an end-to-end lesson plan; **continuous** is an ongoing trajectory such as career or professional education that may contain several lessons. Each lesson carries `standards`, read only from its sidecar (`projects/<slug>/standards.yaml`, decided at planning and during sessions): `covered` (exercised by drafted or defended steps), `ahead` (aligned to steps not done) and `pending_review` (candidates not yet accepted or declined); `analytics.standards` totals them. When you summarize the catalog, name covered standards by statement in plain words and say how many are ahead or waiting for review; standards are reference points, never requirements, and show the attribution when you name them. Use `catalog` to archive/restore, set now/next/later/someday priority, rank within a priority, or correct a classification only at the learner's direction.

If the learner has courses or study activity in systems the harness cannot access, offer the academic advisor. It can build a learner-confirmed inventory from their description, pasted list, syllabus, URL, screenshot, certificate or export and add each item with `catalog(action="add_external", ...)`. Never request credentials or claim a platform was inspected without access.

When the learner asks to visualize or explore their knowledge base, check `setup(action="status")`. If smart search is off, explain that the private map requires the optional local embedding model and ask before enabling it. Once on, call `setup(action="knowledge_map", scope="domain")` and point to `KNOWLEDGE-MAP.html`. Offer reflection/reference/all scopes only if the learner wants them, because those views can include their private notes. Explain that the map is a 3D PCA projection of TurboQuant-compressed embeddings: useful for exploration, not a score or literal map of understanding.

## How it works ("how does the education harness work?", "show me how this works")

Read `how-it-works.md` (this folder) only now; it is the sole source for these facts. Use `profile` to fit the answer: a diagram of the loop if visual; their real lesson files if hands-on; a spoken walk-through under a minute, no lists or paths, if listening; one screen of prose otherwise. Plain at civic-overview depth; files and roles at practitioner or advanced. Lead with the loop, then only what bears on their question, then offer one "under the hood" question.

## Expectations from others, and their own

A class, grade, degree program or employer's expectations: `expectations(action="create", origin="external", issuer, context, source)`, source registered in the library first. Extract items as capabilities from what is visibly in the document, cite where each is (`where_in_source`), read them back, then `add(..., confirmed=true)`. Their own standards: draft a few with them from their goals, in their words, keep only what they confirm (`origin="personal"`). Either set is then searched at planning like any standard and named by origin. Principle 19: refuse items that demand belief or allegiance, offer the capability version; never invent items not in the source.

## Every chat

1. Call `where_am_i` once (with `space` if the project instructions name one, and `focus` if the learner named a goal). Don't call it again in the same chat unless they ask where they are.
2. Act on `suggested.move` in the same reply. No card unless they asked for one.

| move | Do |
| --- | --- |
| `continue` | One line on where they are, in plain words, quoting their newest open question or bookmark if there is one. Then load **tutor** and start the step. |
| `begin` | Do not present a lesson yet. Ask what they want to be able to do. Then ask lesson mode, sociability, mastery mode, depth mode and learning context; ask the conditional context detail. Ask one compact background/notation question before loading **plan** and **tutor**. |
| `plan` | Load **plan** for the next part of their goal, then **tutor**. |
| `choose` | They have several goals: ask which one this chat is for, naming each by its goal. |
| `retro`, `zoom-out` | Load **reflect**. |

If the learner says they're walking, driving or only listening, or the chat brings in an earlier spoken exchange, load **tutor** and follow its *Voice sessions* or *Taking in a voice session* part, whatever the move.

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
- `ask_later` lists what isn't known yet. For a fresh learner, goal, `lesson_mode`, `sociability`, `mastery_mode`, `depth_mode`, `learning_context`, its required detail, and one topic-specific background/notation question come before content.

## Fresh-start calibration

- Treat a project title or `focus` as a topic, not proof of a learning goal or prior knowledge.
- Keep onboarding conversational and compact: first the desired capability; then the kickoff and sociability choices; then the smallest useful calibration of prerequisites and notation comfort. Combine the latter two turns when the question remains easy to answer. Do not infer calculus or matrix notation comfort from one technically correct remark.
- Ask the kickoff choice in plain language: **structured** means an end-to-end lesson plan; **semi-structured** means short segments that adjust to the learner's direction; **free-form** follows whatever question the learner has. Save the answer as `lesson_mode` through `profile`.
- Ask the sociability choice in the same turn when practical: **group** collaboration, **guided** work with a tutor/teacher/parent, or **solo** work. Save the answer as `sociability` through `profile`.
- Ask how they want to demonstrate mastery: **written/practical** through writing and doing, **spoken** through oral explanation, or **both**. Save it as `mastery_mode` through `profile`. This chooses the default evidence format; it never creates a grade or makes the optional defense mandatory.
- Ask depth: **civic overview** (plain language, no calculus or code required), **foundational** (core math, optional code), **practitioner** (all four stages), or **advanced** (derivations, assumptions, failure modes and extensions). Save it as `depth_mode`. Civic overview is complete, not remedial.
- Ask the learning context: **job interview**, **school**, **curiosity/personal growth**, or **professional growth**. For school, ask and save `school_level`. For an interview, ask and save `target_role`. For professional growth, ask and save `professional_context` in the learner's words—their role and responsibilities they want to perform better. Curiosity/personal growth needs no justification or follow-up detail. Save the choice as `learning_context` through `profile`.
- Read `standards.matches` before planning quantitative material. Inspect statements, not codes alone. Use relevant standards to identify prerequisites worth checking; ignore irrelevant matches and never let standards determine scope.
- Start below the first unconfirmed prerequisite, with plain language and a tiny example. Introduce symbols only after naming what each symbol means, then check that the representation works for the learner.

## "How should I set this up?"

1. In the Claude app, make one Project per area you're learning ("Intro to Transformers and NN").
2. Optional, in the project's instructions: `Space: <project name>. Education harness: use the start skill at the start of each chat.`
3. Start a chat and say "let's go". When a chat gets long, say "I'm stopping here", then "let's go" in a fresh chat: your place lives in your learning folder, not the chat.

If the harness tools aren't available at all, say so plainly: the harness server didn't start; it needs `uv` installed (https://docs.astral.sh/uv/), then a restart of the app. Then help them without it.
