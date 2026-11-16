# How Education Harness works (reference for the "how does it work?" answer)

Source of truth for explaining the harness to a learner. Curate it; never read it out whole.
Every claim here matches the code; if a learner asks for proof, open the file named.

## The loop, in one breath

You bring something you want to understand. A short plan turns it into a project made of a few steps. You work each step yourself with one tutor, in chat or by voice. Your own words are kept. When a step has your work in it, it's marked drafted; if you want, you explain it in a defense, and a separate checker reviews the record. Projects end with a chance to share what you made, then a look back at what you learned. Next time, you pick up where you left off.

## The parts (by what they do for the learner)

0. **The tour.** A new learner's first lesson is "how this works": five short steps on a topic they pick, each using a real feature (say what you want, note this and look back, hints and answers, bookmark and where am I, a first real plan). Skippable; "show me how this works" starts it again. It lives in `projects/how-this-works/`.

1. **Planning.** Your goal plus your interests become a plan of three to five steps (or one or two, if you'd rather work in segments, or none for a free-form question). Each step says what you'll do, the ideas it uses, and what a strong version shows. Plans come from your project, never from a syllabus. Sources you give (a public URL, a screenshot, a video) can shape it, with where they came from kept.
2. **Working a step.** One voice, the tutor. Examples from what you care about: small enough to work by hand, or, for interview prep and work, realistic in scale, with the rules that generate them stated and the numbers produced by a saved, seeded script. Hints, the answer, or the method are there whenever you ask; looking is logged, never held against you. Numbers are run before they're stated. Everyday words used as technical terms are defined first. Explorers (one-screen interactive apps) are built when an idea turns on a quantity you can vary.
3. **Keeping your words.** Questions, confusions, insights, attempts and the sentences you want to keep are saved as notes, linked to the step. Slips are kept only if you say so.
4. **Status.** Not started → seen → drafted (your own work exists) → defended (only after a defense the checker reviewed, with a three-part checklist). Seeing a solution never blocks moving on.
5. **Standards (optional).** If you load the open math standards, the plan records which standards each step touches, when the plan is written, in `projects/<lesson>/standards.yaml`. Candidates suggested at planning are accepted or declined then. If your work in a session shows another one, it's added with your words. When a step is drafted or defended, its standards are marked exercised, with the date. Reports and the catalog read only that file, so the same work always reports the same standards. Standards are reference points; they never set the project.
5a. **Expectations.** A class, grade, program or employer's expectations (external, with who set them and the source document) and your own standards (personal, in your words) are kept in `.private/expectations/`, searchable beside the common standards and labeled by origin. Items are added only after you confirm them.
6. **Coming back.** Bookmarks hold your thinking and the next move. `MAP.md` shows where you are. "Where am I?" opens it.
7. **Looking back.** Reports fit how you're using it (computer, phone, voice only). If anyone else is with you, a parent, tutor or group, the harness asks you first before saying anything about how you're doing, and shares only what you agree to.
   **Portfolio pieces (optional, any lesson):** your explanation and your work packaged as a GitHub repository folder, a self-contained web page, a post, or another format, in `projects/<lesson>/portfolio/`, with privacy flags checked first. You publish it yourself.
   Also: run-throughs of past ideas, a journal by day, a retrospective when a project ends, and a progress report on growth, strengths and what's next, quoting you. No grades, scores or comparisons.
8. **Organizing.** The catalog lists every lesson and longer trajectory, with priority, ranking, archive, and the standards each touches. The journey map shows the path. A knowledge map (optional, needs smart search) shows connections across your notes.

## Who does what

- **Tutor:** the one voice you hear. Teaches, keeps your words, marks drafted.
- **Planner:** writes the plan and the standards sidecar. Can work out solutions out of the tutor's sight if you ask.
- **Validator (checker):** only during a defense you asked for. Writes questions, then judges the reviewed record. Never talks to you.
- **Mentor:** the voice of reports, retrospectives and "zoom out" conversations.
- **Academic advisor (optional):** helps organize many lessons, or brings in courses from other tools you describe.

## Where everything lives (all in `~/learning` on your computer)

- `MAP.md` (top of the folder), `goals/<goal>/JOURNEY.html` (one per goal), and `views/` (`JOURNEY.html` for all goals, `CATALOG.html`, `KNOWLEDGE-MAP.html`): views, regenerated from your records. Project folders stay flat under `projects/`, so a project can move between goals without its files moving.
- `projects/<lesson>/portfolio/`: portfolio pieces, if you made any.
- `projects/<lesson>/program.yaml`: the plan. `progress.yaml`: status of each step. `standards.yaml`: the standards sidecar. `solutions/`: worked solutions, if any.
- `.private/` (git-ignored): your profile (`learner.yaml`), expectation sets, notes and journal, bookmarks, defenses and handoffs, retrospectives, reports, catalog settings, the search index.
- What you say in chat is processed by the model provider, under its terms. Nothing is posted anywhere by the harness.

## What it will never do

Grade you, compare you with anyone, post for you, delete your files, change your profile without your yes, let standards decide what you learn, or tell you what to believe. It follows Wikipedia's neutral point of view: views attributed, due weight, reliable sources.

## Who's in charge

It runs on your computer and is open source, so you (or whoever installed it) control it and are responsible for how it's used; the maintainer can't see or supervise any copy. Its own stance, after Dewey: encouragement without flattery, growth, maturity, and good faith toward others.

## How to look under the hood

- "Show me my files for <lesson>": open program.yaml, progress.yaml, standards.yaml.
- "Why did you mark that drafted?": the step's attempts in progress.yaml.
- "Where did that standard come from?": its `via` (cited, concept-link, chosen) and `decided` entry in standards.yaml.
- "What's in my profile?": profile, shown in full; change it by asking.
- `PRINCIPLES.md` in the harness: the rules it follows, which are enforced by tools and which are intentions.
- The README: install, tools and status.
