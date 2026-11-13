"""A run-through of past learnings: the learner's own words, brought back to say again.

``deck()`` gathers one card per concept the learner has words on (their ``keep`` notes,
insights pinned to the concept, and confusions they later answered, as then-and-now pairs),
plus a card for each insight kept on a step without a concept. Cards they have never
run through come first, then the ones run through longest ago, so a review drifts toward
what has had the least attention. ``mark()`` records a run-through in
``.private/review.yaml`` and keeps what they said this time as a new note on the concept,
so their wording can be compared across run-throughs. No scores: a run-through is
practice, never a test (principle 4).
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from .core import Workspace

WORDS_PER_CARD = 3


class Review:
    def __init__(self, ws: "Workspace"):
        self.ws = ws

    @property
    def _file(self) -> Path:
        return self.ws.private / "review.yaml"

    def _log(self) -> dict:
        from .core import _read_yaml
        return (_read_yaml(self._file, {}) or {}).get("cards", {})

    def _cards(self) -> dict[str, dict]:
        """card id -> card, built from every note in the learner's words."""
        board = self.ws.board
        notes = self.ws.journey._notes()            # newest first
        by_id = {n["id"]: n for n in notes}
        cards: dict[str, dict] = {}

        def card(cid: str, title: str) -> dict:
            return cards.setdefault(cid, {"card": cid, "title": title, "your_words": [], "insights": [],
                                          "then_and_now": [], "projects": [], "first_at": ""})

        names = board._names()
        for n in notes:
            kind, concept = n["kind"], (n.get("concept") or "").strip()
            if kind not in ("keep", "insight", "confusion", "question"):
                continue
            if kind in ("confusion", "question"):
                later = by_id.get(n.get("resolved_by", ""))
                if not later:                      # still open: that's for the tutor, not a review
                    continue
            if concept:
                slug = board._slug(concept)
                c = card(f"concept:{slug}", names.get(slug, concept))
            elif kind == "insight":
                c = card(f"note:{n['id']}", n["text"][:60])
            else:
                continue
            if kind == "keep":
                c["your_words"].append({"at": n["at"], "text": n["text"]})
            elif kind == "insight":
                c["insights"].append({"at": n["at"], "text": n["text"]})
            else:
                c["then_and_now"].append({"then": n["text"], "now": by_id[n["resolved_by"]]["text"]})
            if n.get("project") and n["project"] not in c["projects"]:
                c["projects"].append(n["project"])
            if not c["first_at"] or n["at"] < c["first_at"]:
                c["first_at"] = n["at"]
        return cards

    def deck(self, project: str = "", concept: str = "", limit: int = 8) -> dict:
        """The next cards to run through, least-recently-reviewed first."""
        cards = self._cards()
        if concept:
            want = f"concept:{self.ws.board._slug(concept)}"
            cards = {k: v for k, v in cards.items() if k == want}
        if project:
            cards = {k: v for k, v in cards.items() if project in v["projects"]}
        log = self._log()
        out = []
        for cid, c in cards.items():
            seen = log.get(cid, {})
            c["your_words"] = c["your_words"][:WORDS_PER_CARD]
            c["insights"] = c["insights"][:WORDS_PER_CARD]
            c["then_and_now"] = c["then_and_now"][:WORDS_PER_CARD]
            c["last_reviewed"] = seen.get("last", "")
            c["times_reviewed"] = seen.get("times", 0)
            out.append(c)
        out.sort(key=lambda c: (c["last_reviewed"] != "", c["last_reviewed"], c["first_at"]))
        result: dict[str, Any] = {"cards": out[:max(1, limit)], "total": len(out),
                                  "never_reviewed": sum(1 for c in out if not c["times_reviewed"])}
        if not out:
            result["note"] = ("Nothing to run through yet: notes kept with 'remember this', insights, and "
                              "answered questions become review cards.")
        return result

    def mark(self, card: str, said: str = "", project: str = "", step: str = "") -> dict:
        """Record a run-through of one card; keep what they said this time on the concept."""
        from .core import HarnessError, _now, _write_yaml
        if not card:
            raise HarnessError("Which card was run through? Pass its card id from the review deck.")
        if card not in self._cards():
            raise HarnessError(f"No review card '{card}'. Get the deck with look_back(kind='review').")
        data = {"schema": 1, "cards": self._log()}
        entry = data["cards"].setdefault(card, {"times": 0})
        entry["times"] = entry.get("times", 0) + 1
        entry["last"] = _now().isoformat(timespec="minutes")
        _write_yaml(self._file, data)
        out: dict[str, Any] = {"card": card, "times_reviewed": entry["times"], "last_reviewed": entry["last"]}
        if (said or "").strip() and card.startswith("concept:"):
            saved = self.ws.board.remember(card.split(":", 1)[1], f"Run-through: {said.strip()}", project, step)
            out["kept"] = saved["saved"]
        return out
