# Explorers

How the tutor builds an interactive page for an idea with a dial. Learned from real sessions; each rule below fixed something a learner found confusing. Principles: 1, 7.

## When

- Early in the step, before text has had a chance to fail. Define the step's `terms` on the page itself.
- Publish it as an artifact when the app offers one, so the learner can come back to it, and keep its link in their notes (`note(kind="thought")`). Point to it from then on instead of re-explaining in paragraphs.
- First lessons (the tour's s1, a new learner's first small lesson): if the idea has a dial or a process you can watch run, the explorer comes in the same reply as the idea, inline in the chat (a widget), so the learner plays before reading. Placement comes first (`placement.md`), and every label, control and number on screen uses only words the learner already has or that the screen defines beside it. Keep it to one screen and one or two controls, run its numbers in code first, and offer once to keep it as a page they can come back to.
- Not in a voice session.

## Shape

- Start from `explorer-template.html` in the tutor skill's folder (one level up): a working scene engine (fixed 16:9 stage, Back/Next and arrow keys, scene dots, Present and Study modes, prediction boxes, a Details drawer). Replace the scenes; keep the engine.
- Scenes, not scrolling panels. One fixed screen that never scrolls, one scene at a time (a picture, a one-sentence caption, the scene's one control, Back/Next with arrow keys), so the learner never scrolls to a setting and back to its effect. A Present mode (picture and caption only, video-sized type) and a Study mode (prediction boxes and a Details drawer with the algebra and definitions). Predict-then-reveal is a scene state: "?" on the picture, then Next reveals it.
- Design one picture of the whole idea before building, not a panel per sub-idea: the same object transforms step by step ("Next step" changes one thing), at a consistent scale (say when it zooms), with one row of numbers that fills in as each step is reached. For a picture the learner has said isn't working, propose the redesign in a few lines and ask before rebuilding; don't patch.
- Build each picture from objects the learner has already met (the table's rows become rectangles), never a new abstraction introduced to explain them. Name both axes on any chart, keep the caption to one line, and let the picture carry the explanation rather than a paragraph beside it.
- Run the starting case through the same formula as every later case, with its values shown (n = 1: ÷ 1², ÷ √1), so the general rule is visible from the first step rather than appearing later.
- Every control must visibly change something on screen; anything random reruns itself when a setting changes. Before publishing, drive it in a real browser (move each slider, press each button) and fix what doesn't respond.
- Show change as change: a single run's result with an arrow and how far above or below the target it landed, and a running table of past runs to compare settings.
- Size pictures so small values stay visible (cut a fixed shape into tiles rather than drawing a vanishing one), and size charts so the shape of a distribution shows at every setting.
- Label every quantity on the picture itself: each length, area and cut gets its number and its name, so the picture can be read without the text beside it.
- Reveal derivations one line at a time, each line with its numbers and why it follows, and ask for a prediction before each line.
- Practice boxes never give the answer away in the prompt: ask for the result, then the reason in the learner's words; hints point back to a panel instead of stating the rule.

## Check before showing

- The page's data comes from the lesson's saved generator or a closed form (`examples.md`): the starting scene matches its `expected.json`, and any randomness is seeded so a setting reproduces.
- Run the page's numbers against the formula (a simulation's spread against the standard error, a factoring at several values).
- Drive it in a real browser at a laptop size (for example 1280 × 720): every scene, every state, every control. Confirm nothing scrolls and the console has no errors. Look at one screenshot of each scene before publishing.
- For an explorer the learner wants to show other people (a video, a team), get a fresh-context review of its UX first (an agent that hasn't seen it being built), and propose the changes to the learner before rebuilding.
