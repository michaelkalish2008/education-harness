"""Neutral point of view guardrail (principle 19).

The harness follows the content standards Wikipedia holds itself to: a neutral point of view
(significant views represented fairly and in proportion to reliable sources), verifiability
(claims a learner could check), and no promotion. A learning goal names what a learner will know,
do, explain or evaluate; it never prescribes what they must believe, whom they must support or what
they must condemn. Teaching a contested view is fine; requiring assent to it is not.

check() is a tool-level gate on the text that defines learning: plan steps and expectation items.
It is deliberately narrow (belief, allegiance and condemnation demanded of the learner), so ordinary
goals pass; the skills carry the fuller standard for everything the tutor says.
"""
from __future__ import annotations

import re

_SUBJECT = r"(?:(?:students?|learners?|pupils?|children|participants?|you|i|we|the (?:student|learner))\s+)?"
_MODAL = r"(?:(?:will|shall|should|must|can|are expected to|is expected to|is able to|be able to|learns? to|come to)\s+)?"
_DEMANDS = [
    r"believes?\b", r"accepts? that\b", r"agrees? that\b", r"agrees? with\b", r"affirms?\b", r"profess(?:es)?\b",
    r"embrace(?:s)?\b", r"pledges?\b", r"(?:be|are|is|remain) loyal\b", r"swears?\b", r"condemns?\b",
    r"denounces?\b", r"reject(?:s)? the (?:lies|false|evil)", r"adopts? the (?:view|belief|position|ideology) that\b",
    r"be convinced\b", r"recognizes? the (?:superiority|inferiority)\b", r"loves? (?:the|our) (?:party|leader|nation)\b",
    r"supports? (?:the|our) (?:party|leader|movement|cause|government|candidate)\b",
    r"oppos(?:e|es) (?:the|our) (?:party|leader|movement|cause|government|candidate)\b",
]
_PATTERN = re.compile(r"^\s*" + _SUBJECT + _MODAL + r"(?:" + "|".join(_DEMANDS) + r")", re.IGNORECASE)
_LOADED = re.compile(r"\b(?:the truth (?:about|that) .{0,40}(?:hoax|lie|conspiracy)|propaganda for|"
                     r"(?:prove|show) that .{0,60} (?:is|are) (?:evil|subhuman|inferior|superior))", re.IGNORECASE)


def check(text: str) -> str | None:
    """Return a plain explanation if the text demands belief, allegiance or condemnation, else None."""
    t = (text or "").strip()
    if not t:
        return None
    if _PATTERN.search(t) or _LOADED.search(t):
        return ("This asks the learner to hold a belief or take a side, not to know, do, explain or evaluate "
                "something. The harness follows Wikipedia's neutral point of view: rephrase as a capability, "
                "e.g. 'explain the main arguments for and against …, with sources' or 'evaluate the evidence "
                "for …'.")
    return None


def check_all(label: str, texts: list[str]) -> list[str]:
    return [f"{label}: \"{t[:80]}\" — {msg}" for t in texts if (msg := check(t))]
