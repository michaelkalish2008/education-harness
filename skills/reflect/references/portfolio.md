# Portfolio pieces (optional, any lesson)

Any lesson, at any depth or mode, can end in something the learner shows: a GitHub repository, a web page, a post, or another format they name. Never required; a lesson is complete without one. Triggers: a plan with `audience_format: portfolio`, the share-out step, or "make this a portfolio piece", "put this on GitHub", "make a web page of this", "turn this into a post".

## Build it from their words and work

1. **Ask where, once:** GitHub, a web page, a post, or something else (slides, a notebook, a PDF). Use `audience_where` from the plan if it's set.
2. **The learner explains first.** Draft from their explanation, notes (`look_back(project=…)`) and share drafts; edit only for order, clarity and length. Their work files (code, data, explorers they built in `work/`) are included as they are. Worked solutions in `solutions/` are not theirs and stay out.
3. **Save:** `save_doc(kind="portfolio", project, target, title, files={path: text}, include=[project-relative paths])`. Writes `projects/<lesson>/portfolio/<target>/`; building again updates it.
4. **Show every `privacy_flags` item** and anything else private (other people's names or data, journal text, workplace material that isn't theirs). Fix on their word.
5. **They publish it themselves.** Give the returned `publish` steps. Run a command or publish a page only when they ask you to in this chat, never by default. Afterwards: `note(kind="shared", how="posted", where, link, project)`.

## What each target holds

- **github:** `README.md` with, in this order: the question (their words); what they built; how it works, in their explanation; how to run it (exact commands, with the uv project's `pyproject.toml` if code is included); what they learned and one limit they'd name; sources and credits; optional line that an AI tutor helped. Code and small data files beside it. A `.gitignore` is added. Optional `index.html` for GitHub Pages.
- **web:** one self-contained `index.html`: inline CSS, no trackers or outside scripts unless an explorer needs them, readable on a phone, alt text for images, headings in order. Same sections as the README, shorter. An explorer can be embedded as part of the page.
- **post:** `post.md` (or `post.txt` for plain-text sites): a hook from their question, the one idea in their words, one picture or number that makes it concrete, what's next, link to the repo or page if there is one. Fit the site's length.
- **other:** whatever files the format needs (slides as Markdown, a notebook, LaTeX), same sections.

Check before saving: run every number and code path, `check_links` for every link, attribute contested views (19). Standards, if named, use statements in plain words with attribution.
