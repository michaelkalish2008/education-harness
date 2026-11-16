# The tour: an opt-in guided lesson on using the harness

Offered, never forced: new learners start with `welcome.md`. The tour is for anyone who says "show me how this works". It teaches the harness by using it: every step works a real feature on a tiny topic the learner picks, so the tour is also their first real lesson. Project `how-this-works`, steps s1–s5. Whole tour: about ten minutes; one to three turns per step.

## Starting

- "Show me how this works" / "take the tour", any time: `setup(action="tour")`, then step s1 in the same reply. Open with the four-step picture from `welcome.md` (a widget if one is available, one line otherwise), then one line: "This short lesson shows you how this works by using it on something you pick." Keep every turn in plain words, about grade 5, with one question at a time.
- If their first message already asks for something ("teach me the chain rule"), that is the s1 topic. Don't ask again.
- "Skip the tour", "I know how this works", or they clearly want to dive in: `setup(action="skip_tour")`, then follow move `begin` (`onboarding.md`). Never insist. Mid-tour, "skip the rest" jumps to s5.
- Fit the modality: listening only, read `../../tutor/references/voice.md` and replace anything visual (s4's MAP.md becomes "your place is kept in a file on your computer; just say 'where am I?'").

## The script (teach the phrase, have them use it, mark the step)

Each step: name the phrase in one line, let the learner say or do it, let the tool do its real work, then `note(kind="attempt", project="how-this-works", step=…, text=<what they did, their words>)`, `set_status(…, "drafted")`, and `setup(action="introduced", feature=…)` for each phrase taught. Say "that's how it works every time" once, not every step. Use **goal**, **step**, **note**, **bookmark**; never tools, skills or MCP.

1. **s1 · Say what you want.** Ask what they're curious about, anything, kept small. Teach one tiny idea from it with an example small enough to work by hand (lens checks apply: run numbers, cite passages). If the idea has a dial or a process you can watch run (a random walk, a sampler, a rate), show it as a one-screen explorer in the same reply when a widget tool exists (`../../tutor/references/explorers.md`, First lessons), so they try it before reading about it. They work it. Point out: you said what you wanted, and that became a step. If they share an interest, propose it with `profile` and accept on their yes.
2. **s2 · Keep your words.** "Say 'note this' and then anything: a question, a hunch, half a thought." Save it (`note`, kind fits). Then "say 'look back'" and bring it back with `look_back(project="how-this-works")`, quoting them. Point out: notes are in your words, never rewritten, and they come back in any later chat.
3. **s3 · Help, your way.** Give a tiny puzzle on their topic. Invite "hint", then "show me the answer" or "show me the method": `reveal` each (work it out and check it, since there's no pre-written solution). Offer a sibling problem; their attempt on it is the step's work. Point out: looking is logged, never held against you; a step is **drafted** when your own work exists, and an optional defense, if you ever want one, is a conversation, not a test.
4. **s4 · Leave and come back.** "Say 'bookmark this'." Save with `bookmark(action="save", label, thinking, next_move)` in their words. Then "say 'where am I?'" and show the help card (`SKILL.md`). Name `MAP.md` in their learning folder (`~/learning`) as the same view, readable with the app closed. Point out: your place lives in your learning folder, not the chat, so a fresh chat plus "let's go" picks up here.
5. **s5 · Make it yours.** Ask what they want to learn for real (it may be s1's topic, grown). Ask only what `welcome.md` Turn 2 asks, if `ask_later` still lists it; everything else waits until it matters (`onboarding.md`). Then load **plan** and agree a first plan. Ask once, lightly: "When it's done, want it to end in something you can show, like a GitHub repository, a web page or a post? Optional, and you can decide later." Record a yes in the plan (`audience_format="portfolio"`, `audience_where`). Their goal and agreement are the step's attempt; mark s5 drafted.

## Ending

One line: what they now know how to do ("say what you want, note this, look back, ask for hints, bookmark, where am I"), and "next time, just say 'let's go'." Then start step one of their new plan if there's time, or `bookmark` and stop. The tour gets no retrospective. It stays in the catalog as a finished lesson; "show me how this works" starts it again.
