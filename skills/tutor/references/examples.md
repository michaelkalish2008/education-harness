# Examples

How the tutor and planner build an example. Learned from an interview-prep session: a by-hand toy (4 shifts, 3 nurses, "nurses pick labeled shifts first") read to the learner as a tiny sample ("insufficient data to show causality"), and it left out where the nurses came from. A seeded simulation at marketplace scale, shown as one small table, is what worked. Principles: 0, 7, 8.

## Rules

1. **Realistic where the learner will meet it.** For `job-interview` and `professional-growth`, the example mirrors how the problem appears in practice: realistic scale (thousands of units, not four), the real mechanism, plausible magnitudes (rates and effect sizes a practitioner would believe), and posed the way an interviewer or colleague would pose it ("We labeled half the shifts in a test and fill rose; what does launching to every shift do?"). A by-hand miniature is allowed only as a stepping stone, and is said to be one: "a miniature to see the mechanism; the realistic version comes next." Other contexts keep tiny, by-hand examples from the learner's interests.
2. **State the generating rules first.** Before any number: what exists (units and counts: 2,000 cities, 40 shifts and 25 nurses per city), how choices are made (each nurse picks one shift or nothing, by logit choice), what the treatment changes (a label adds utility), and what is shared (both halves draw on the same nurses). Then say which kind it is:
   - **Thought experiment, stipulated rules:** the numbers are consequences of the rules, not estimates, so sample size is not the question; say so.
   - **Noisy sample:** say n, where the noise comes from, and that uncertainty is part of the question.
   A missing rule is a missing fact: if the learner asks "where do they come from?", the rules were incomplete; add the rule and say it was missing.
3. **Data is regenerable.** It comes from a seeded script (the seed is a named constant at the top) or a closed form. Same seed, same numbers, every time.
4. **Every number shown was run.** Run the script and copy its output; never type, round by eye or estimate a number. Save the generator with the lesson so it can be re-verified:
   - `projects/<project>/examples/<step>/example.py`: the rules in its docstring, the seed and sizes as constants, and one printed JSON object of the outputs.
   - `projects/<project>/examples/<step>/expected.json`: exactly what it printed, the numbers the learner saw.
   - Before reusing a number in a later session, or when the learner doubts one, re-run and compare with `expected.json`; a mismatch is said and corrected (principle 7).
   - Without file access, keep the script, seed and outputs in `note(kind="thought", project, step)`. Without any way to run code, use a closed form checked with a computation connector, or label the numbers unchecked.
5. **Small on screen.** One table (a few rows: the naive estimate, the true effect, the comparison that explains the gap) and one question. The full output stays in the file. The learner-format rules still apply (one question per reply, terms defined first).

## Example first

Every explanation starts from a concrete example, whatever the topic: a concept, a formula, a line of code, a step in a derivation, a learner's question. Learned from a session where the learner asked about each line of a simulation loop and got a table of plain-words definitions first, with the trace after; he could repeat it but not hold it. The order is:

1. **The example, in real values.** A specific case the learner can see: actual numbers from running the code or formula, or a named, concrete situation for non-numeric ideas.
2. **What they notice.** One question about it.
3. **The idea named.** The rule, term or line meaning, tied back to the values already on screen ("that 0 in `w` is `np.where` switching off a filled shift").

An abstract definition, a list of what each line does, or a symbol with no value behind it is never the first thing shown. If no example comes to mind, build one before answering.

## Explaining code

When the learner asks what code does, or says they can read it but not internalize it:

- Run it on the smallest input that still shows the mechanism (labeled as a miniature, rule 1), with print statements inside the loop, and show one table: one row per pass, one column per variable that changes.
- Point to a specific cell before explaining the line that made it. Explain only the lines the learner asked about, one idea per turn when they're lost.
- Unfamiliar functions (`np.where`, `np.append`, `rng.choice`) get a one-line call on tiny literal inputs with its output (`np.append([2, 1], 5)` gives `[2, 1, 5]`), not a description.
- Save the trace script under `examples/<step>/` like any generator, so the learner can rerun it and change the input.

## Shape of a generator

```python
"""Rules (stipulated): CITIES cities, each with SHIFTS shifts and NURSES nurses from one shared pool.
Each nurse picks one shift or the outside option by logit choice; a label adds LIFT utility."""
import json, numpy as np
SEED, CITIES, SHIFTS, NURSES, LIFT = 7, 2000, 40, 25, 0.5
rng = np.random.default_rng(SEED)
# ... simulate the test world (half labeled) and both global worlds (none, all) with the same rules ...
print(json.dumps({"seed": SEED, "naive_test_estimate": ..., "true_global_effect": ...}))
```

For an explorer, the page's starting scene shows the numbers in `expected.json`, and any randomness on the page uses a seeded generator so a setting reproduces.

`examples/` is lesson material beside the plan, like the learner's own code, not learner state: it is not under `solutions/` or `.private/`, and the generator is visible to the learner.
