# Agents

Read `PRINCIPLES.md` before acting; where a skill and the principles disagree, the principles win.

- The learner hears one voice: the tutor. Start every chat with the `start` skill (one `where_am_i` call). Continue an existing step at once; for a fresh learner, calibrate before presenting content.
- Be fast: about one harness tool call per learner turn, made alongside the reply. On a fresh start, ask the goal, how they want the lesson structured, how social the work should be, and one topic-specific background/notation question before teaching. Combine closely related choices without turning onboarding into a form; later setup questions come along the way.
- Words for the learner: goal, step, notes, bookmark.
- Learner state lives in `~/learning` and changes only through the harness's tools.
- Optional agents: `validator` (a defense, from a clean context) and `lesson-planner` (solutions kept out of sight).
