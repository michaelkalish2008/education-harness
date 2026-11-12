# First real sessions: test plan

Three sessions on the shipped plugin, and one baseline. The point is to find what to cut.

## Setup

- Install `education-harness.plugin` (0.6.0) and restart the Claude app. Remove `education-harness-test` if it's still installed.
- Make sure the app runs the **bundled** server, not the repo: leave `EH_DEV` unset. If `uv` isn't installed, install it first (otherwise the launcher falls back to the repo venv, which isn't what learners get).
- Start fresh: move `~/learning` aside (for example to `~/learning-before-0.6`).
- Use a Claude Project, "Intro to Transformers and NN".

## Sessions

| | When | Say | What should happen |
| --- | --- | --- | --- |
| **A** | Day 1, new chat | "Explain the chain rule." | Teaching starts in the first reply with a tiny example. At most one question about you, and only when it fits. A plan appears without ceremony. |
| **B** | Day 2, new chat | "Let's go." | One line on where you are, quoting a note or bookmark from A correctly; the next step starts. |
| **C** | Any day, new chat in "Computational Phenomenology" | "Let's look at one passage on care in Heidegger." | It cites the passage, keeps text and interpretation apart, and doesn't feel like a problem set. |
| **Baseline** | Day 1, plain Claude in a Project, harness disabled | Same as A | For comparison. |

## Watch

- Your turns before the first real learning (A).
- Tool calls per turn, and how long replies take.
- Cards, offers or questions you didn't want.
- Whether B brings back your words, accurately and usefully.
- Any refused or wrong tool calls.
- What you noted yourself, and whether it came back.

## Kill criteria

- **A:** more than two turns before learning starts → cut setup further.
- **More than about one tool call per turn on median, or more than three to open a chat** → merge or drop calls.
- **B doesn't restore your place and your words** → fix that before anything else; it's the core.
- **After B, you can't name one thing the harness did better than the baseline** → cut to `where_am_i`, `note`, `look_back` and `bookmark`, and one skill.
- **C feels like a problem set** → drop steps and solutions for the philosophy lens; keep only notes and passages.

## Record

After each session, a few lines: what felt good, what felt clunky, anything you'd cut. Those notes decide 0.7.
