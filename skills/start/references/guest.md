# Guest mode

For "let's try this as a guest", "guest mode", "let my friend try it", or the owner testing a first run. Principles: 1, 18.

## Starting

- `setup(action="guest_start", feature=<their first name, if offered>)`, then `where_am_i` again: it now answers for the guest (a brand-new learner, move `welcome`, and a `guest` field). Follow `welcome.md`, or `tour.md` if they asked how it works.
- Say once, in plain words: "This is a fresh space just for you. It's deleted when you're done, unless you ask to keep it for a day or a week."

## While a guest is active

- Everything about the owner stays out: no Claude memory, user preferences or profile facts about the owner, no past chats, no other goals. Use only what the guest says in this chat. If the app injects memory about the owner, don't apply it.
- Never save memory about the guest (they aren't the account holder). The harness tools are the only place their work lives.
- "Keep this for a day" / "for a week": `setup(action="guest_keep", feature="day"|"week")`, and say when it will be deleted.

## Ending

- "I'm done", "end guest mode", or the owner taking back over: ask once whether to keep it (no, a day, a week). Then `setup(action="guest_end", feature=""|"day"|"week")`. Default is delete.
- If kept, give the guest the line to come back: "say 'resume guest <id>'", which runs `setup(action="guest_resume", feature=<id>)`.
- Unended sessions delete themselves after two idle hours; kept ones at their day or week.
