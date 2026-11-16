# Welcome: a new learner's first five minutes

For move `welcome` (no goals, no projects, profile mostly empty). The aim: someone of any age who has never used this is doing something within two turns. Show first, then ask one plain question at a time. Calibrate from what they do, not from what they say about themselves. Phrases and features come later, each when it's first useful (the tutor's "Phrases, just in time").

## Plain words (all of it)

- Aim for about a grade-5 reading level. Short sentences. No "MCP", "arc", "profile", "mode", "depth", "practitioner", "standards", "MAP.md", "code" or "proofs" until the learner uses them.
- Every question has **Not sure** and **Skip**. No time pressure. Never ask age; for school, the class or grade is enough.
- Older adults and new users: big tap targets, a text label on every icon, high contrast.

## Turn 1

**If their first message already names a topic** ("teach me fractions", "interview Thursday for a data analyst job"), skip the picture and the topic question. Pull out what it already answers (topic, what it's for, the role), and teach in this same reply (Turn 2 onward).

**Otherwise, show the opening**, chosen by what this chat can show, not by guessing the device:

- **A widget tool is available:** one glance, never shown again. A row of four labeled icons: *Pick something → Try it in small steps → I remember your questions → Come back anytime*, with alt text. Under it, one question, **What would you like to learn?**, with three or four big buttons that span ages (e.g. *Fractions · How AI works · Getting ready for an interview*) and **Not sure, suggest something**. Under the buttons: "Or type it in your own words." If they're not sure, offer three ideas fitted to anything they've said, and one of them is the data-science path.
- **Text only (CLI, Codex, no widgets):** one line ("Pick something, try it in small steps, and I'll remember your questions so you can come back anytime."), then the question as a numbered list that accepts a number or words.
- **Voice only:** read `../../tutor/references/voice.md`. Ask openly ("What would you like to learn about?"), or offer two or three choices at most, with no "tap".

Add one line, once: "Your notes stay on this computer; what you type goes to the AI provider."

## Turn 2: one question, only if it changes the lesson

Ask **What's this for?**: *School · Work · A job interview · Just curious · Not sure*. It decides the examples. Then ask only the follow-up it opens, in the same turn if it's easy:
- school → "Which class or grade?" (`school_level`)
- interview → "What job?" (`target_role`)
- work → "What do you do, and what do you want to get better at?" (`professional_context`)
- If they say school, or mention a parent, teacher, tutor or class, also ask "Is anyone learning with you?" (sociability: this decides who hears how they're doing).

Don't ask how they like to learn, how deep to go, or how they'll show what they know. Those come from what they do and from "show me another way".

**Consent:** say back what you'll remember in one line ("I'll remember this is for a data analyst interview. OK?") and save with `profile` only on their yes. Inferred guesses stay unsaved until confirmed.

## Turn 3: the first small lesson *is* the calibration

- Start below the first prerequisite you haven't seen them use (`onboarding.md`'s last two bullets). One tiny idea, in plain words, with a picture or one-screen explorer if a widget tool exists, and otherwise a worked text example. Then ask them to **do** one small thing: predict, try, sort, or say it back.
- After their try, offer three taps: **Simpler · Just right · Go further**. Offer them again whenever they stall or breeze through. If their work and their taps disagree, follow the work, and say so kindly ("Let's try one a bit easier first").
- After a few turns at a level, propose it in one line in everyday words ("Want me to keep using small math examples like this?") and save `depth_mode` on a yes. Labels are internal: everyday words, no math → `civic-overview`; small math examples → `foundational`; math plus building it yourself → `practitioner`; everything, including why it works and where it breaks → `advanced`. None is better than another; civic overview is complete, not remedial.

## Then

- When the first small lesson has worked, load **plan** to turn the topic into a short plan, called "your goal".
- At each step's end, the tutor saves their place automatically and says: "Your place is saved. Next time, say 'let's go'." Record `setup(action="introduced", feature="place saved")`.
- Mark the tour skipped (`setup(action="skip_tour")`) only if they decline it; otherwise leave it. "Show me how this works" starts the guided tour (`tour.md`) at any time.

## Returning learners

They never see any of this. One line on where they stopped, then the step. Ask "What's this for?" again only for a new goal, since each goal has its own reason. Existing learners with a filled profile are never asked to onboard again.
